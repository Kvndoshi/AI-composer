// Options page script

const DEFAULT_SETTINGS = {
  apiUrl: 'http://localhost:8000',
  llmModel: 'claude-sonnet-4-5-20250929',
  defaultTone: 'professional',
  autoStore: true
};

document.addEventListener('DOMContentLoaded', loadSettings);
document.getElementById('saveBtn').addEventListener('click', saveSettings);
document.getElementById('resetBtn').addEventListener('click', resetSettings);

async function loadSettings() {
  const settings = await chrome.storage.sync.get(Object.keys(DEFAULT_SETTINGS));
  
  document.getElementById('apiUrl').value = settings.apiUrl || DEFAULT_SETTINGS.apiUrl;
  document.getElementById('llmModel').value = settings.llmModel || DEFAULT_SETTINGS.llmModel;
  document.getElementById('defaultTone').value = settings.defaultTone || DEFAULT_SETTINGS.defaultTone;
  document.getElementById('autoStore').checked = settings.autoStore !== undefined ? settings.autoStore : DEFAULT_SETTINGS.autoStore;
}

async function saveSettings() {
  const settings = {
    apiUrl: document.getElementById('apiUrl').value,
    llmModel: document.getElementById('llmModel').value,
    defaultTone: document.getElementById('defaultTone').value,
    autoStore: document.getElementById('autoStore').checked
  };
  
  await chrome.storage.sync.set(settings);
  
  showMessage('Settings saved successfully!', 'success');
}

async function resetSettings() {
  await chrome.storage.sync.set(DEFAULT_SETTINGS);
  await loadSettings();
  showMessage('Settings reset to defaults', 'success');
}

function showMessage(text, type) {
  const messageDiv = document.getElementById('message');
  messageDiv.textContent = text;
  messageDiv.className = `message ${type}`;
  messageDiv.style.display = 'block';
  
  setTimeout(() => {
    messageDiv.style.display = 'none';
  }, 3000);
}

