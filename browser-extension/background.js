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
      sendToAria2(downloadItem);
    }
  });
});

function sendToAria2(downloadItem) {
  fetch('http://localhost:6801/jsonrpc', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: '1',
      method: 'aria2.addUri',
      params: [[downloadItem.url], {"pause": "true"}]
    })
  }).then(response => {
    chrome.downloads.cancel(downloadItem.id);
  }).catch(error => {

  });
}
