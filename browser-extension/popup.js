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
