let startTime = Date.now();

chrome.runtime.onInstalled.addListener(function (details) {
  if (details.reason === 'install') {
    chrome.storage.sync.set({ enabled: true, cookieTransferFile: true, cookieTransferVideo: true });
  }
});

chrome.downloads.onCreated.addListener(function (downloadItem) {
  var downloadTime = new Date(downloadItem.startTime).getTime();
  const id = downloadItem.id;
  const maxRetries = 5;
  const retryDelay = 200;

  if (downloadTime < startTime) {
    return;
  }

  // Firefox does not provide totalBytes immediately, so we need to wait for it to become available.

  let retries = 0;

  function checkDownloadSize() {
    chrome.downloads.search({ id }, function (results) {
      if (!results || results.length === 0) return;
      const item = results[0];

      if (item.totalBytes !== -1 || retries >= maxRetries) {
        chrome.storage.sync.get(['enabled', 'downloadSize'], async function (data) {
          const minSize = (data.downloadSize || 0) * 1048576;
          console.log('Min Download Size:', minSize);
          console.log('Download Size:', item.totalBytes);

          // Defaults to sending to Varia if totalBytes cannot be determined
          if (data.enabled && (item.totalBytes >= minSize || retries >= maxRetries)) {
            sendToAria2(item, "file");
          }
        });
      } else {
        retries++;
        setTimeout(checkDownloadSize, retryDelay);
      }
    });
  }
  checkDownloadSize();
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

const aria2ProtocolAllowlist = new RegExp(/^(http|https|ftp|sftp):\/\//, "i");

function filterUrl(url) {
  return aria2ProtocolAllowlist.test(url);
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

  console.log("Headers sent to aria2:", headers);

  // If downloadUrl is set and fails the filter
  if (downloadUrl && !filterUrl(downloadUrl)) {
    return;
  }

  try {
    const response = await fetch("http://localhost:6801/jsonrpc", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: "1",
        method: "aria2.addUri",
        params: jsonParams
      })
    });

    const data = await response.json();
    console.log("Aria2 response:", data);

    if (downloadType === "file" && data.result) {
      chrome.downloads.cancel(downloadItem.id);
    }

  } catch (error) {
    console.error("Failed to send to Aria2:", error);
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