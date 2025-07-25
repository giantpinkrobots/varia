document.addEventListener('DOMContentLoaded', function () {
  var toggleSwitch = document.getElementById('toggleSwitch');
  chrome.storage.sync.get('enabled', function(data) {
    toggleSwitch.checked = data.enabled;
  });
  toggleSwitch.addEventListener('change', function () {
    var enabled = this.checked;
    chrome.storage.sync.set({enabled: enabled});
  });
});

document.querySelector('.video-button').addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'VIDEO_BUTTON_CLICKED' });
});