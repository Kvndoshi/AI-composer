// Background service worker for AI Message Composer

const API_BASE_URL = 'http://localhost:8000';

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('🔔 BACKGROUND: Message received', request.action);
  
  if (request.action === 'rewriteMessage') {
    console.log('   → Handling rewrite message...');
    handleRewriteMessage(request.data)
      .then(response => {
        console.log('   → Success, sending response back');
        sendResponse({ success: true, data: response });
      })
      .catch(error => {
        console.error('   → Error occurred:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'storeConversation') {
    handleStoreConversation(request.data)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'storeProfile') {
    handleStoreProfile(request.data)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'summarize') {
    handleSummarize(request.data)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'chat') {
    handleChat(request.data)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'getSettings') {
    chrome.storage.sync.get(['apiUrl', 'llmModel'], (items) => {
      sendResponse({ 
        success: true, 
        data: {
          apiUrl: items.apiUrl || API_BASE_URL,
          llmModel: items.llmModel || 'fallback'
        }
      });
    });
    return true;
  }
  
  console.warn('   → Unknown action:', request.action);
});

// Handle message rewrite request
async function handleRewriteMessage(data) {
  const startTime = performance.now();
  console.log('\n' + '─'.repeat(60));
  console.log('📡 BACKGROUND: Received rewrite request from content script');
  console.log('─'.repeat(60));
  
  const { platform, userInput, conversationContext, recipient } = data;
  
  console.log('   → Platform:', platform);
  console.log('   → Recipient:', recipient);
  console.log('   → User input length:', userInput?.length);
  console.log('   → Context messages:', conversationContext?.length);
  
  // Get API URL from settings
  const settings = await chrome.storage.sync.get(['apiUrl']);
  const apiUrl = settings.apiUrl || API_BASE_URL;
  console.log('   → API URL:', apiUrl);
  
  try {
    const fetchStart = performance.now();
    console.log('\n🌐 BACKGROUND: Calling backend API...');
    console.log('   → Endpoint:', `${apiUrl}/api/rewrite`);
    
    const requestBody = {
      platform,
      user_input: userInput,
      conversation_context: conversationContext,
      recipient
    };
    console.log('   → Request body size:', JSON.stringify(requestBody).length, 'bytes');
    
    const response = await fetch(`${apiUrl}/api/rewrite`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });
    
    const fetchTime = performance.now() - fetchStart;
    console.log('   → Fetch completed in:', fetchTime.toFixed(2) + 'ms');
    console.log('   → Response status:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('   ❌ API error response:', errorText);
      throw new Error(`API request failed: ${response.statusText}`);
    }
    
    const parseStart = performance.now();
    const jsonData = await response.json();
    const parseTime = performance.now() - parseStart;
    
    console.log('   → JSON parsed in:', parseTime.toFixed(2) + 'ms');
    console.log('   → Rewritten message length:', jsonData.rewritten_message?.length);
    console.log('   → Context used:', jsonData.context_used);
    
    const totalTime = performance.now() - startTime;
    console.log('\n✅ BACKGROUND: Request complete');
    console.log('   → Total background time:', totalTime.toFixed(2) + 'ms');
    console.log('   → Sending response back to content script');
    console.log('─'.repeat(60));
    
    return jsonData;
  } catch (error) {
    const totalTime = performance.now() - startTime;
    console.error('\n❌ BACKGROUND: Error after', totalTime.toFixed(2) + 'ms');
    console.error('   → Error type:', error.name);
    console.error('   → Error message:', error.message);
    console.error('   → Error stack:', error.stack);
    console.log('─'.repeat(60));
    throw error;
  }
}

// Handle conversation storage
async function handleStoreConversation(data) {
  const { platform, recipient, message, isOutgoing } = data;

  if (!message || !message.trim()) {
    return { status: 'skipped' };
  }
  
  const settings = await chrome.storage.sync.get(['apiUrl']);
  const apiUrl = settings.apiUrl || API_BASE_URL;
  
  try {
    const response = await fetch(`${apiUrl}/api/store-conversation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        platform,
        recipient,
        message,
        is_outgoing: isOutgoing,
        timestamp: new Date().toISOString()
      })
    });
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error storing conversation:', error);
    throw error;
  }
}

async function handleStoreProfile(data) {
  const settings = await chrome.storage.sync.get(['apiUrl']);
  const apiUrl = settings.apiUrl || API_BASE_URL;

  // Get cookies for the profile URL to enable authenticated scraping
  let cookies = [];
  try {
    const url = new URL(data.profile_url);
    cookies = await chrome.cookies.getAll({ domain: url.hostname });
    console.log(`📦 Retrieved ${cookies.length} cookies for ${url.hostname}`);
  } catch (error) {
    console.warn('Failed to get cookies:', error);
  }

  const response = await fetch(`${apiUrl}/api/store-profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...data,
      cookies: cookies  // Pass cookies to backend
    })
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return await response.json();
}

async function handleSummarize(data) {
  const settings = await chrome.storage.sync.get(['apiUrl']);
  const apiUrl = settings.apiUrl || API_BASE_URL;

  // Get cookies for the URL to enable authenticated scraping
  let cookies = [];
  try {
    const url = new URL(data.url);
    cookies = await chrome.cookies.getAll({ domain: url.hostname });
    console.log(`📦 Retrieved ${cookies.length} cookies for ${url.hostname}`);
  } catch (error) {
    console.warn('Failed to get cookies:', error);
  }

  const response = await fetch(`${apiUrl}/api/summarize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...data,
      cookies: cookies  // Pass cookies to backend
    })
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return await response.json();
}

async function handleChat(data) {
  const settings = await chrome.storage.sync.get(['apiUrl']);
  const apiUrl = settings.apiUrl || API_BASE_URL;

  const response = await fetch(`${apiUrl}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return await response.json();
}

// Context menu disabled to avoid missing API errors in some environments
// If you need the context menu, ensure the "contextMenus" permission is present
// and re-enable the guarded block below.
// chrome.runtime.onInstalled.addListener(() => {
//   if (chrome.contextMenus?.create) {
//     chrome.contextMenus.create({
//       id: 'rewriteMessage',
//       title: 'Rewrite with AI',
//       contexts: ['editable']
//     });
//     console.log('✓ BACKGROUND: Context menu created');
//   } else {
//     console.warn('⚠️  BACKGROUND: contextMenus API not available');
//   }
// });
//
// chrome.contextMenus?.onClicked?.addListener((info, tab) => {
//   if (info.menuItemId === 'rewriteMessage') {
//     chrome.tabs.sendMessage(tab.id, { action: 'triggerRewrite' });
//   }
// });

