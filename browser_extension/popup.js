document.addEventListener('DOMContentLoaded', function () {
  var toggleSwitch = document.getElementById('toggleSwitch');
  var downloadSizeInput = document.getElementById('downloadSize');
  var cookieTransferFileCheckbox = document.getElementById('cookieTransferFile');
  var cookieTransferVideoCheckbox = document.getElementById('cookieTransferVideo');

  chrome.storage.sync.get(['enabled', 'downloadSize', 'cookieTransferFile', 'cookieTransferVideo'], function (data) {
    toggleSwitch.checked = data.enabled;
    downloadSizeInput.value = data.downloadSize || 0;
    cookieTransferFileCheckbox.checked = data.cookieTransferFile || false;
    cookieTransferVideoCheckbox.checked = data.cookieTransferVideo || false;
  });

  toggleSwitch.addEventListener('change', function () {
    var enabled = this.checked;
    chrome.storage.sync.set({ enabled: enabled });
  });

  downloadSizeInput.addEventListener('change', function () {
    var downloadSize = this.value;
    chrome.storage.sync.set({ downloadSize: downloadSize });
  });

  cookieTransferFileCheckbox.addEventListener('change', function () {
    var cookieTransferFile = this.checked;
    chrome.storage.sync.set({ cookieTransferFile: cookieTransferFile });
  });

  cookieTransferVideoCheckbox.addEventListener('change', function () {
    var cookieTransferVideo = this.checked;
    chrome.storage.sync.set({ cookieTransferVideo: cookieTransferVideo });
  });
});

document.querySelector('.video-button').addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'VIDEO_BUTTON_CLICKED' });
});
