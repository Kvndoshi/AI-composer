// Popup script for AI Message Composer

document.addEventListener('DOMContentLoaded', async () => {
  await checkConnection();
  await loadStats();
  
  document.getElementById('testConnection').addEventListener('click', testConnection);
  document.getElementById('openOptions').addEventListener('click', openOptions);
});

async function checkConnection() {
  const statusDiv = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  
  try {
    const settings = await chrome.storage.sync.get(['apiUrl']);
    const apiUrl = settings.apiUrl || 'http://localhost:8000';
    
    const response = await fetch(`${apiUrl}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    
    if (response.ok) {
      statusDiv.className = 'status connected';
      statusText.textContent = '✓ Connected to backend';
    } else {
      throw new Error('Backend not responding');
    }
  } catch (error) {
    statusDiv.className = 'status disconnected';
    statusText.textContent = '✗ Backend not connected';
  }
}

async function testConnection() {
  const button = document.getElementById('testConnection');
  button.textContent = 'Testing...';
  button.disabled = true;
  
  await checkConnection();
  
  button.textContent = 'Test Connection';
  button.disabled = false;
}

function openOptions() {
  chrome.runtime.openOptionsPage();
}

async function loadStats() {
  const stats = await chrome.storage.local.get(['messageCount', 'conversationCount']);
  
  document.getElementById('messageCount').textContent = stats.messageCount || 0;
  document.getElementById('conversationCount').textContent = stats.conversationCount || 0;
}

