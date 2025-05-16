let startTime = Date.now();

chrome.runtime.onInstalled.addListener(function (details) {
  if (details.reason === "install") {
    chrome.storage.sync.set({ enabled: true });
  }
});

chrome.downloads.onCreated.addListener(function (downloadItem) {
  var downloadTime = new Date(downloadItem.startTime).getTime();
  if (downloadTime < startTime) {
    return;
  }

  chrome.storage.sync.get("enabled", function (data) {
    if (data.enabled) {
      sendToAria2(downloadItem);
    }
  });
});

chrome.tabs.onActivated.addListener(async function (activeInfo) {
  try {
    if ("mozInnerScreenX" in window) {
      // Thanks Firefox...:')
      tab = await browser.tabs.get(activeInfo.tabId);
    } else {
      tab = await chrome.tabs.get(activeInfo.tabId);
    }

    if (tab.url != "") {
      handleContextMenu(tab);
    }
  } catch (error) {
    console.error(error);
  }
});

chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tab) {
  handleContextMenu(tab);
});

chrome.contextMenus.onClicked.addListener(function (info, tab) {
  if (info.menuItemId == "varia-video-download") {
    sendVideoToAria(tab.url);
  }
});

async function handleContextMenu(tab) {
  if (tab.url.includes("youtube.com/watch")) {
    chrome.contextMenus.create({
      title: "Download video with Varia",
      id: "varia-video-download",
    });
  } else {
    try {
      await chrome.contextMenus.remove("varia-video-download");
    } catch (error) {
      console.log("No menu item.");
    }
  }
}

function sendToAria2(downloadItem) {
  fetch("http://localhost:6801/jsonrpc", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: "1",
      method: "aria2.addUri",
      params: [[downloadItem.url], { pause: "true" }],
    }),
  })
    .then((response) => {
      chrome.downloads.cancel(downloadItem.id);
    })
    .catch((error) => {});
}

function sendVideoToAria(url) {
  fetch("http://localhost:6803/video", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: url,
    }),
  })
    .then((response) => {
      console.log("Sent video to Varia");
    })
    .catch((error) => {
      console.error(error);
    });
}
