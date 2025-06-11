let startTime = Date.now();

chrome.runtime.onInstalled.addListener(function(details) {
  if (details.reason === 'install') {
    chrome.storage.sync.set({enabled: true});
  }
});

chrome.downloads.onCreated.addListener(function(downloadItem) {
  var downloadTime = new Date(downloadItem.startTime).getTime();
  if (downloadTime < startTime) {
    return;
  }

  chrome.storage.sync.get('enabled', function(data) {
    if (data.enabled) {
      sendToAria2(downloadItem, "file");
    }
  });
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
