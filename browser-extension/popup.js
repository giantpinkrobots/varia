document.addEventListener('DOMContentLoaded', function () {
  var toggleSwitch = document.getElementById('toggleSwitch');
  var downloadSizeInput = document.getElementById('downloadSize');

  chrome.storage.sync.get(['enabled', 'downloadSize'], function(data) {
    toggleSwitch.checked = data.enabled;
    downloadSizeInput.value = data.downloadSize || 0;
  });

  toggleSwitch.addEventListener('change', function () {
    var enabled = this.checked;
    chrome.storage.sync.set({enabled: enabled});
  });
  downloadSizeInput.addEventListener('change', function () {
    var downloadSize = this.value;
    chrome.storage.sync.set({downloadSize: downloadSize});
  });
});

document.querySelector('.video-button').addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'VIDEO_BUTTON_CLICKED' });
});