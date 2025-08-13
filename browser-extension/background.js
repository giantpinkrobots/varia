let startTime = Date.now();

chrome.runtime.onInstalled.addListener(function(details) {
  if (details.reason === 'install') {
    chrome.storage.sync.set({enabled: true});
  }
});

chrome.downloads.onCreated.addListener(function(downloadItem) {
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
    chrome.downloads.search({ id }, function(results) {
      if (!results || results.length === 0) return;
      const item = results[0];

      if (item.totalBytes !== -1 || retries >= maxRetries) {
        chrome.storage.sync.get(['enabled', 'downloadSize'], function(data) {
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

function sendToAria2(downloadItem, downloadType) {
  let jsonParams;

  if (downloadType === "file") {
    jsonParams = [[downloadItem.url], { pause: "true" }];
  } else if (downloadType === "video") {
    jsonParams = [[downloadItem], {
      pause: "true",
      out: "varia-video-download.variavideo"
    }];
  }

  fetch("http://localhost:6801/jsonrpc", {
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
  })
  .then(response => response.json())
  .then(data => {
    console.log("Aria2 response:", data);
    if (downloadType === "file") {
      chrome.downloads.cancel(downloadItem.id);
    }
  })
  .catch(error => {
    console.error("Failed to send to Aria2:", error);
  });
}
