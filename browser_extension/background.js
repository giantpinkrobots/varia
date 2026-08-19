let startTime = Date.now();

async function initializeStartTime() {
  const data = await chrome.storage.local.get(['startTime']);
  if (!data.startTime) {
    chrome.storage.local.set({ startTime });
  } else {
    startTime = data.startTime;
  }
}

initializeStartTime();

chrome.runtime.onStartup.addListener(function () {
  startTime = Date.now();
  chrome.storage.local.set({ startTime });

  // Clean up forwarded download IDs from the previous time because we don't need them anymore, obviously
  chrome.storage.local.get(null, (items) => {
    try {
      const keysToRemove = Object.keys(items || {}).filter(k => k.startsWith('forwarded:'));
      if (keysToRemove.length) {
        chrome.storage.local.remove(keysToRemove);
      }
    } catch (e) {
      // Ignore the errors here
    }
  });
});

chrome.runtime.onInstalled.addListener(function (details) {
  if (details.reason === 'install') {
    chrome.storage.sync.set({ enabled: true, cookieTransferFile: false, cookieTransferVideo: false });
  }
});

const aria2cAddresses = [ // Adding both 127.0.0.1 and localhost to be super extra sure
  "http://127.0.0.1:6801/jsonrpc",
  "http://localhost:6801/jsonrpc"
];

const aria2ProtocolAllowlist = new RegExp(/^(http|https|ftp|sftp):\/\//, 'i');
const downloadProcessing = new Set();

function makeDelay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getDownloadItemById(id) {
  return new Promise((resolve) => {
    chrome.downloads.search({ id }, function (results) {
      resolve(results && results.length ? results[0] : null);
    });
  });
}

function getStorage(keys) {
  return new Promise((resolve) => {
    chrome.storage.sync.get(keys, resolve);
  });
}

async function processDownloadById(id, initialItem = null) {
  // To prevent the sometimes duplication of downloads
  const forwardedKey = `forwarded:${id}`;
  const alreadyForwarded = await new Promise((resolve) => {
    chrome.storage.local.get(forwardedKey, (res) => resolve(Boolean(res && res[forwardedKey])));
  });
  if (alreadyForwarded) return;

  if (downloadProcessing.has(id)) {
    return;
  }

  downloadProcessing.add(id);
  try {
    let item = initialItem;
    const maxRetries = 8; // Have some wiggle room for retries
    const retryDelay = 250;
    let retries = 0;

    while (retries <= maxRetries) {
      if (!item) {
        item = await getDownloadItemById(id);
      }

      if (!item) {
        retries++;
        await makeDelay(retryDelay);
        continue;
      }

      const downloadTime = item.startTime ? new Date(item.startTime).getTime() : 0;
      if (downloadTime < startTime) {
        return;
      }

      const isTorrentFile = item.filename && item.filename.toLowerCase().endsWith(".torrent");
      if (item.totalBytes !== -1 || retries >= maxRetries || isTorrentFile) {
        break;
      }

      retries++;
      item = null;
      await makeDelay(retryDelay);
    }

    if (!item) {
      console.warn("Download item is not available to process: ", id);
      return;
    }

    const data = await getStorage(["enabled", "downloadSize"]);
    const minSize = (data.downloadSize || 0) * 1048576;
    console.log("Min Download Size: ", minSize);
    console.log("Download Size: ", item.totalBytes);

    const isTorrentFile = item.filename && item.filename.toLowerCase().endsWith(".torrent");
    if (
      data.enabled && (
        item.totalBytes >= minSize ||
        item.totalBytes === -1 ||
        isTorrentFile // .torrent files need to be exempt from the set minimum download size
      )
    ) {
      await sendToAria2(item, "file");
    }
  } finally {
    downloadProcessing.delete(id);
  }
}

chrome.downloads.onCreated.addListener(function (downloadItem) {
  processDownloadById(downloadItem.id, downloadItem);
});

chrome.downloads.onChanged.addListener(function (downloadDelta) {
  if (downloadDelta.totalBytes || downloadDelta.state || downloadDelta.filename || downloadDelta.url) {
    processDownloadById(downloadDelta.id);
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'VIDEO_BUTTON_CLICKED') {
    console.log('Video button clicked');
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const currentTab = tabs[0];
      sendToAria2(currentTab.url, "video");
      console.log('Video sent: ' + currentTab.url);
    });
  }
});

function filterUrl(url) {
  return aria2ProtocolAllowlist.test(url);
}

async function sendJsonRpcRequest(body) {
  let errorMessage = null;
  for (const endpoint of aria2cAddresses) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        errorMessage = new Error(`HTTP ${response.status} - ${response.statusText}`);
        console.warn("aria2c RPC connection failed here: ", endpoint, errorMessage);
        continue;
      }

      const data = await response.json();
      return data;
    } catch (e) {
      errorMessage = e;
      console.warn("aria2c RPC connection failed here: ", endpoint, e);
    }
  }

  throw errorMessage || new Error("aria2c RPC request failed for all.");
}

async function sendToAria2(downloadItem, downloadType) {
  let jsonParams, downloadUrl;

  const cookieHeader = await setCookiesString(downloadItem, downloadType);
  const headers = cookieHeader ? [cookieHeader] : [];

  if (downloadType === "file") {
    downloadUrl = downloadItem.url;

    jsonParams = [[downloadUrl], {
      pause: "true",
      header: headers
    }];

  } else if (downloadType === "video") {

    jsonParams = [[downloadItem], {
      pause: "true",
      out: "varia-video-download.variavideo",
      header: headers
    }];
  }

  // If downloadUrl is set and fails the filter
  if (downloadUrl && !filterUrl(downloadUrl)) {
    return;
  }

  try {
    const data = await sendJsonRpcRequest({
      jsonrpc: "2.0",
      id: "1",
      method: "aria2.addUri",
      params: jsonParams
    });

    console.log("aria2c response: ", data);

    if (downloadType === "file") {
      if (data && data.result) {
        chrome.downloads.cancel(downloadItem.id);
        try {
          // Mark this download as forwarded to avoid duplicates
          chrome.storage.local.set({ [`forwarded:${downloadItem.id}`]: { url: downloadItem.url, gid: data.result } });
        } catch (e) {
          // Ignore the storage errors here
        }
      } else {
        console.warn("aria2c did not return a result for this download: ", downloadItem.id, data);
      }
    }
  } catch (e) {
    console.error("Failed to send to aria2c: ", e);
  }
}

async function setCookiesString(downloadItem, downloadType) {
  const data = await chrome.storage.sync.get(['cookieTransferFile', 'cookieTransferVideo']);

  if (downloadType === "file") {
    if (!data.cookieTransferFile) {
      return null;
    } else {
      return await getCookies(downloadItem.url, downloadType);
    }
  } else if (downloadType === "video") {
    if (!data.cookieTransferVideo) {
      return null;
    } else {
      return await getCookies(downloadItem, downloadType);
    }
  }
}

async function getCookies(downloadUrl, downloadType) {
  const url = new URL(downloadUrl);
  const cookies = await chrome.cookies.getAll({
    url: url.toString()
  });

  if (!cookies.length) return null;

  if (downloadType === "file") {
    const cookieString = cookies
      .map(c => `${c.name}=${c.value}`)
      .join("; ");

    return `Cookie: ${cookieString}`;
  } else if (downloadType === "video") {
    const json = JSON.stringify(cookies);

    return btoa(json);
  }
}