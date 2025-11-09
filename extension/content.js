// Content script for AI Message Composer
// Handles platform detection, DOM scraping, and UI injection

class MessageComposer {
  constructor() {
    this.platform = this.detectPlatform();
    this.initialized = false;
    this.activeInput = null;
    this.latestDraft = '';
    this.sidebarWrapper = null;
    this.sidebar = null;
    this.chatContainer = null;
    this.chatLog = [];
    this.observer = null;
    
    if (this.platform) {
      this.init();
    }
  }
  
  detectPlatform() {
    const hostname = window.location.hostname;
    
    if (hostname.includes('linkedin.com')) {
      return 'linkedin';
    } else if (hostname.includes('mail.google.com')) {
      return 'gmail';
    }
    
    // Return 'web' for all other websites
    return 'web';
  }
  
  init() {
    console.log(`AI Message Composer initialized for ${this.platform}`);
    
    // Wait for page to be fully loaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }
  
  setup() {
    // Inject button styles
    this.injectStyles();
    
    // Start observing DOM for message inputs
    this.observeMessageInputs();

    // Inject floating sidebar UI
    this.initSidebar();

    // Observe send events to store outgoing messages automatically
    this.observeSendEvents();
    
    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'triggerRewrite') {
        this.handleRewrite();
      }
    });
    
    this.initialized = true;
  }
  
  injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .ai-composer-fab-wrapper {
        position: fixed;
        top: 80px;
        right: 24px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 12px;
        pointer-events: none;
      }
      
      .ai-composer-fab-wrapper > * {
        pointer-events: auto;
      }

      .ai-composer-fab {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 12px 24px rgba(37, 99, 235, 0.35);
        user-select: none;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        touch-action: none;
      }

      .ai-composer-fab:hover {
        transform: translateY(-2px);
        box-shadow: 0 16px 30px rgba(37, 99, 235, 0.45);
      }

      .ai-composer-sidebar {
        width: 320px;
        min-width: 260px;
        max-width: 600px;
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.12);
        padding: 16px;
        font-family: 'Segoe UI', sans-serif;
        display: flex;
        flex-direction: column;
        gap: 12px;
        resize: horizontal;
        overflow: auto;
      }

      .ai-composer-sidebar h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #0a2540;
      }

      .ai-composer-sidebar.hidden {
        display: none;
      }

      .ai-composer-sidebar button.ai-composer-action {
        width: 100%;
        padding: 10px 12px;
        border: none;
        border-radius: 8px;
        background: #0a65cc;
        color: #fff;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s ease;
      }

      .ai-composer-sidebar button.ai-composer-action:hover {
        background: #084fa0;
      }

      .ai-composer-chat-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 8px;
      }

      .ai-composer-chat-container.hidden {
        display: none;
      }

      .ai-composer-chat-container textarea {
        width: 100%;
        min-height: 80px;
        border-radius: 8px;
        border: 1px solid #d0d5dd;
        padding: 8px;
        font-family: inherit;
        resize: vertical;
      }

      .ai-composer-chat-log {
        max-height: 160px;
        overflow-y: auto;
        background: #f8fafc;
        border-radius: 8px;
        padding: 8px;
        font-size: 13px;
        color: #1f2937;
      }

      .ai-composer-chat-log .entry {
        margin-bottom: 8px;
      }

      .ai-composer-chat-log .entry span {
        display: block;
        font-weight: 600;
        color: #0a65cc;
      }

      .ai-composer-actions {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .ai-composer-actions.hidden {
        display: none;
      }

      .ai-composer-summarizer-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 8px;
      }

      .ai-composer-summarizer-container.hidden {
        display: none;
      }

      .ai-composer-summarizer-container h4 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #0a2540;
      }

      .ai-composer-summarizer-container textarea {
        width: 100%;
        min-height: 80px;
        border-radius: 8px;
        border: 1px solid #d0d5dd;
        padding: 8px;
        font-family: inherit;
        resize: vertical;
      }

      .ai-composer-summarizer-log {
        max-height: 200px;
        overflow-y: auto;
        background: #f8fafc;
        border-radius: 8px;
        padding: 8px;
        font-size: 13px;
        color: #1f2937;
      }

      .ai-composer-back-btn {
        padding: 8px 12px;
        border: 1px solid #d0d5dd;
        border-radius: 8px;
        background: #ffffff;
        color: #0a2540;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
      }

      .ai-composer-back-btn:hover {
        background: #f8fafc;
        border-color: #0a65cc;
      }

      .ai-composer-chat-entry {
        margin-bottom: 8px;
        padding: 8px;
        border-radius: 6px;
        position: relative;
      }

      .ai-composer-chat-entry strong {
        display: block;
        margin-bottom: 4px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .ai-composer-chat-you strong {
        color: #0a65cc;
      }

      .ai-composer-chat-assistant {
        background: #f0fdf4;
        border-left: 3px solid #059669;
      }

      .ai-composer-chat-assistant strong {
        color: #059669;
      }

      .ai-composer-chat-system strong {
        color: #dc2626;
      }

      .ai-composer-copy-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        padding: 4px 8px;
        background: #ffffff;
        border: 1px solid #d0d5dd;
        border-radius: 4px;
        font-size: 11px;
        cursor: pointer;
        opacity: 0;
        transition: all 0.2s ease;
        color: #6b7280;
        font-weight: 500;
      }

      .ai-composer-chat-entry:hover .ai-composer-copy-btn {
        opacity: 1;
      }

      .ai-composer-copy-btn:hover {
        background: #f3f4f6;
        border-color: #059669;
        color: #059669;
      }

      .ai-composer-copy-btn.copied {
        background: #059669;
        color: white;
        border-color: #059669;
      }

      .ai-composer-message-text {
        word-wrap: break-word;
        white-space: pre-wrap;
        line-height: 1.5;
      }
    `;
    document.head.appendChild(style);
  }
  
  observeMessageInputs() {
    // Use MutationObserver to detect when message inputs appear
    this.observer = new MutationObserver(() => {
      this.checkForMessageInputs();
    });
    
    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Initial check
    this.checkForMessageInputs();
  }
  
  checkForMessageInputs() {
    const inputs = this.findMessageInputs();
    
    inputs.forEach(input => {
      if (!input.dataset.aiComposerAttached) {
        this.attachToInput(input);
        input.dataset.aiComposerAttached = 'true';
      }
    });
  }
  
  findMessageInputs() {
    if (this.platform === 'linkedin') {
      return this.findLinkedInInputs();
    } else if (this.platform === 'gmail') {
      return this.findGmailInputs();
    }
    return [];
  }
  
  findLinkedInInputs() {
    const inputs = [];
    
    // LinkedIn messaging input
    const messageInputs = document.querySelectorAll('.msg-form__contenteditable, [contenteditable="true"][role="textbox"]');
    messageInputs.forEach(input => {
      if (input.closest('.msg-form') || input.closest('[data-control-name="messaging"]')) {
        inputs.push(input);
      }
    });
    
    // LinkedIn post composer
    const postInputs = document.querySelectorAll('.ql-editor[contenteditable="true"]');
    postInputs.forEach(input => {
      if (input.closest('.share-box') || input.closest('[data-test-share-box]')) {
        inputs.push(input);
      }
    });
    
    return inputs;
  }
  
  findGmailInputs() {
    const inputs = [];
    
    // Gmail compose window
    const composeInputs = document.querySelectorAll('[role="textbox"][aria-label*="Message Body"], [role="textbox"][g_editable="true"]');
    composeInputs.forEach(input => {
      inputs.push(input);
    });
    
    return inputs;
  }
  
  attachToInput(input) {
    input.addEventListener('focus', () => {
      this.activeInput = input;
    });

    input.addEventListener('input', () => {
      this.activeInput = input;
      this.latestDraft = this.getInputText(input);
    });

    this.latestDraft = this.getInputText(input);
  }
  
  async handleRewrite(input = null) {
    const flowStartTime = performance.now();
    console.log('═'.repeat(60));
    console.log('🚀 STEP 1: Rewrite button clicked');
    console.log('═'.repeat(60));
    
    if (!input) {
      input = document.activeElement;
      console.log('   → Using active element as input');
    }
    
    if (!input || !this.isMessageInput(input)) {
      console.error('❌ No valid message input found');
      console.log('   Input element:', input);
      console.log('   Is contentEditable:', input?.isContentEditable);
      console.log('   Tag name:', input?.tagName);
      return;
    }
    
    console.log('✓ Step 1 complete:', (performance.now() - flowStartTime).toFixed(2) + 'ms');
    
    // STEP 2: Get text from textbox
    const step2Start = performance.now();
    console.log('\n📝 STEP 2: Getting text from textbox...');
    const userInput = this.getInputText(input);
    console.log('   → Input text:', userInput?.substring(0, 50) + (userInput?.length > 50 ? '...' : ''));
    console.log('   → Text length:', userInput?.length || 0);
    
    if (!userInput || userInput.trim().length === 0) {
      console.error('❌ No text in input field');
      alert('Please write a message first!');
      return;
    }
    console.log('✓ Step 2 complete:', (performance.now() - step2Start).toFixed(2) + 'ms');
    
    // Get button and show loading state
    const button = input.parentElement?.querySelector('.ai-composer-button');
    const originalButtonText = button ? button.innerHTML : '';
    if (button) {
      button.disabled = true;
      button.classList.add('loading');
      button.innerHTML = '<div class="ai-composer-spinner"></div> Rewriting...';
      console.log('   → Button updated to loading state');
    }
    
    try {
      // STEP 3: Scrape context
      const step3Start = performance.now();
      console.log('\n🔍 STEP 3: Scraping context (max 1 second)...');
      console.log('   → Platform:', this.platform);
      
      const contextPromise = this.scrapeConversationContext(input);
      const recipientPromise = Promise.resolve(this.getRecipient());
      
      // Wait max 1 second for context scraping
      const conversationContext = await Promise.race([
        contextPromise,
        new Promise(resolve => {
          setTimeout(() => {
            console.log('   ⚠️  Context scraping timeout (1s), continuing without context');
            resolve([]);
          }, 1000);
        })
      ]);
      
      const recipient = await recipientPromise;
      console.log('   → Recipient:', recipient);
      console.log('   → Context messages found:', conversationContext.length);
      if (conversationContext.length > 0) {
        console.log('   → First message:', conversationContext[0].text?.substring(0, 30) + '...');
      }
      console.log('✓ Step 3 complete:', (performance.now() - step3Start).toFixed(2) + 'ms');
      
      // STEP 4: Send to background → API → LLM
      const step4Start = performance.now();
      console.log('\n📤 STEP 4: Sending to background script → API → LLM...');
      console.log('   → Platform:', this.platform);
      console.log('   → Recipient:', recipient);
      console.log('   → User input length:', userInput.length);
      console.log('   → Context messages:', conversationContext.length);
      
      const requestData = {
        action: 'rewriteMessage',
        data: {
          platform: this.platform,
          userInput,
          conversationContext,
          recipient
        }
      };
      console.log('   → Sending message to background script...');
      
      const response = await chrome.runtime.sendMessage(requestData);
      
      console.log('   → Response received from background');
      console.log('   → Response success:', response?.success);
      console.log('✓ Step 4 complete:', (performance.now() - step4Start).toFixed(2) + 'ms');
      
      if (response && response.success) {
        // STEP 5: Get rewritten text back
        const step5Start = performance.now();
        console.log('\n✅ STEP 5: Got rewritten text from LLM');
        const rewrittenText = response.data.rewritten_message;
        console.log('✅ Got response, updating textbox', { length: rewrittenText.length });
        
        this.setInputText(input, rewrittenText);
        this.latestDraft = rewrittenText;
        
        console.log('✓ Step 5 complete:', (performance.now() - step5Start).toFixed(2) + 'ms');
        
        // STEP 6: Replace text in textbox
        const step6Start = performance.now();
        console.log('\n🔄 STEP 6: Replacing text in textbox...');
        console.log('   → Input field type:', input.isContentEditable ? 'contentEditable' : input.tagName);
        
        this.setInputText(input, rewrittenText);
        
        console.log('✓ Step 6 complete:', (performance.now() - step6Start).toFixed(2) + 'ms');
        
        // STEP 7: Show success feedback
        console.log('\n🎉 STEP 7: Showing success feedback');
        
        // Update stats
        this.updateStats('messageCount');
        
        // Store conversation in background (don't wait for it)
        const settings = await chrome.storage.sync.get(['autoStore']);
        if (settings.autoStore) {
          console.log('   → Storing conversation in background');
          this.storeMessage(recipient, rewrittenText, true).catch(err => {
            console.warn('   ⚠️  Failed to store conversation:', err);
          });
        }
        
        // Show success feedback
        if (button) {
          button.innerHTML = '✓ Done!';
          console.log('   → Button updated to "Done!"');
          setTimeout(() => {
            if (button) {
              button.innerHTML = originalButtonText;
              console.log('   → Button restored to original state');
            }
          }, 2000);
        }
        
        const totalTime = performance.now() - flowStartTime;
        console.log('\n' + '═'.repeat(60));
        console.log('✅ REWRITE COMPLETE');
        console.log('   Total time:', totalTime.toFixed(2) + 'ms (' + (totalTime / 1000).toFixed(2) + 's)');
        console.log('═'.repeat(60));
        
      } else {
        const errorMsg = response?.error || 'Unknown error';
        console.error('\n❌ REWRITE FAILED:', errorMsg);
        console.error('   Response:', response);
        alert(`Error: ${errorMsg}`);
        if (button) {
          button.innerHTML = originalButtonText;
        }
      }
    } catch (error) {
      console.error('\n❌ EXCEPTION CAUGHT:', error);
      console.error('   Error name:', error.name);
      console.error('   Error message:', error.message);
      console.error('   Error stack:', error.stack);
      alert(`Failed to rewrite message: ${error.message}`);
      if (button) {
        button.innerHTML = originalButtonText;
      }
    } finally {
      if (button) {
        button.disabled = false;
        button.classList.remove('loading');
        if (!button.innerHTML.includes('Done!')) {
          button.innerHTML = originalButtonText;
        }
      }
      const totalTime = performance.now() - flowStartTime;
      console.log('\n⏱️  Total flow time:', totalTime.toFixed(2) + 'ms');
    }
  }
  
  isMessageInput(element) {
    return element.isContentEditable || 
           element.tagName === 'TEXTAREA' || 
           element.tagName === 'INPUT';
  }
  
  getInputText(input) {
    if (input.isContentEditable) {
      return input.innerText || input.textContent;
    }
    return input.value;
  }
  
  setInputText(input, text) {
    if (input.isContentEditable) {
      // For contentEditable (LinkedIn), use textContent for better compatibility
      input.textContent = text;
      input.innerText = text;
      
      // Set focus and cursor to end
      input.focus();
      const range = document.createRange();
      const selection = window.getSelection();
      range.selectNodeContents(input);
      range.collapse(false);
      selection.removeAllRanges();
      selection.addRange(range);
      
      // Trigger events that LinkedIn/Gmail might be listening to
      input.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
      input.dispatchEvent(new Event('keyup', { bubbles: true, cancelable: true }));
      input.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: true, key: 'Enter' }));
    } else {
      // For textarea/input (Gmail)
      input.value = text;
      input.focus();
      input.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
      input.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
    }
    
    console.log('✅ Text updated in input field');
  }
  
  async scrapeConversationContext(input) {
    if (this.platform === 'linkedin') {
      return this.scrapeLinkedInContext();
    } else if (this.platform === 'gmail') {
      return this.scrapeGmailContext();
    }
    return [];
  }
  
  scrapeLinkedInContext() {
    const messages = [];
    
    try {
      // Find message thread (faster query)
      const messageList = document.querySelector('.msg-s-message-list__container, .msg-s-message-list');
      if (!messageList) return messages;
      
      // Get only visible messages (faster, limit to last 5 for speed)
      const messageElements = Array.from(messageList.querySelectorAll('.msg-s-message-group, .msg-s-event-listitem')).slice(-5);
      
      for (const msgEl of messageElements) {
        const textEl = msgEl.querySelector('.msg-s-event-listitem__body, .msg-s-message-group__text, .msg-s-message-group__text');
        if (textEl) {
          const text = textEl.innerText?.trim() || textEl.textContent?.trim();
          if (text && text.length > 0) {
            messages.push({
              text,
              is_outgoing: msgEl.classList.contains('msg-s-message-group--outgoing'),
              timestamp: new Date().toISOString()
            });
          }
        }
      }
    } catch (error) {
      console.warn('Error scraping LinkedIn context:', error);
    }
    
    return messages;
  }
  
  scrapeGmailContext() {
    const messages = [];
    
    try {
      // Find email thread (limit to last 5 for speed)
      const emailThread = Array.from(document.querySelectorAll('.h7, [data-message-id]')).slice(-5);
      
      for (const emailEl of emailThread) {
        const bodyEl = emailEl.querySelector('[data-message-text], .a3s');
        if (bodyEl) {
          const text = bodyEl.innerText?.trim() || bodyEl.textContent?.trim();
          if (text && text.length > 0) {
            const fromEl = emailEl.querySelector('[email], .gD');
            messages.push({
              text,
              is_outgoing: fromEl?.innerText?.includes('me') || false,
              timestamp: new Date().toISOString()
            });
          }
        }
      }
    } catch (error) {
      console.warn('Error scraping Gmail context:', error);
    }
    
    return messages;
  }
  
  extractTimestamp(element) {
    const timeEl = element.querySelector('time, [data-time], .msg-s-message-group__timestamp');
    if (timeEl) {
      return timeEl.getAttribute('datetime') || timeEl.innerText;
    }
    return new Date().toISOString();
  }
  
  getRecipient() {
    if (this.platform === 'linkedin') {
      return this.getLinkedInRecipient();
    } else if (this.platform === 'gmail') {
      return this.getGmailRecipient();
    }
    return 'unknown';
  }
  
  getLinkedInRecipient() {
    // Try to get recipient name from conversation header
    const header = document.querySelector('.msg-thread__link-to-profile, .msg-overlay-conversation-bubble__title');
    if (header) {
      return header.innerText.trim();
    }
    
    const profileLink = document.querySelector('.msg-thread a[href*="/in/"]');
    if (profileLink) {
      return profileLink.innerText.trim();
    }
    
    return 'LinkedIn Contact';
  }
  
  getGmailRecipient() {
    // Get recipient from To field
    const toField = document.querySelector('[name="to"], .aoD[email]');
    if (toField) {
      return toField.getAttribute('email') || toField.innerText.trim();
    }
    
    // Get from subject line
    const subject = document.querySelector('.hP');
    if (subject) {
      return subject.innerText.trim();
    }
    
    return 'Gmail Contact';
  }
  
  async storeMessage(recipient, message, isOutgoing) {
    try {
      await chrome.runtime.sendMessage({
        action: 'storeConversation',
        data: {
          platform: this.platform,
          recipient,
          message,
          isOutgoing
        }
      });
      
      this.updateStats('conversationCount');
    } catch (error) {
      console.error('Failed to store message:', error);
    }
  }
  
  async updateStats(statName) {
    const stats = await chrome.storage.local.get([statName]);
    const currentValue = stats[statName] || 0;
    await chrome.storage.local.set({ [statName]: currentValue + 1 });
  }

  initSidebar() {
    if (this.sidebarWrapper || !document.body) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'ai-composer-fab-wrapper';

    const fab = document.createElement('div');
    fab.className = 'ai-composer-fab';
    fab.textContent = 'AI';

    const sidebar = document.createElement('div');
    sidebar.className = 'ai-composer-sidebar hidden';
    sidebar.innerHTML = `
      <h3>AI Message Composer</h3>
      <div class="ai-composer-actions">
        <button class="ai-composer-action" data-action="generate">✨ Generate</button>
        <button class="ai-composer-action" data-action="profile">📇 Capture Profile</button>
        <button class="ai-composer-action" data-action="summarize">📝 Summarize Page</button>
        <button class="ai-composer-action" data-action="chat-toggle">💬 Chat</button>
      </div>
      <div class="ai-composer-chat-container hidden">
        <div class="ai-composer-chat-log"></div>
        <textarea class="ai-composer-chat-input" placeholder="Ask about your knowledge graph..."></textarea>
        <button class="ai-composer-action" data-action="chat-send">Send</button>
      </div>
      <div class="ai-composer-summarizer-container hidden">
        <button class="ai-composer-back-btn" data-action="back">← Back</button>
        <h4>Page Summarizer</h4>
        <div class="ai-composer-summarizer-log"></div>
        <textarea class="ai-composer-summarizer-input" placeholder="Ask about this page..."></textarea>
        <button class="ai-composer-action" data-action="summarizer-send">Send</button>
      </div>
    `;

    fab.addEventListener('click', (event) => {
      // Don't toggle sidebar if FAB was just dragged
      if (this._wasDragged) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      
      sidebar.classList.toggle('hidden');
      if (sidebar.classList.contains('hidden')) {
        this.chatContainer?.classList.add('hidden');
      }
    });

    sidebar.addEventListener('click', (event) => {
      const actionBtn = event.target.closest('.ai-composer-action, .ai-composer-back-btn');
      if (!actionBtn) return;
      const action = actionBtn.dataset.action;
      
      if (action === 'generate') {
        this.handleRewrite(this.activeInput);
      } else if (action === 'profile') {
        this.captureProfile();
      } else if (action === 'summarize') {
        this.enterSummarizerMode();
      } else if (action === 'back') {
        this.exitSummarizerMode();
      } else if (action === 'chat-toggle') {
        this.chatContainer?.classList.toggle('hidden');
        if (!this.chatContainer?.classList.contains('hidden')) {
          const textarea = this.sidebar.querySelector('.ai-composer-chat-input');
          textarea?.focus();
        }
      } else if (action === 'chat-send') {
        const textarea = sidebar.querySelector('.ai-composer-chat-input');
        const question = textarea.value.trim();
        if (!question) return;
        this.appendChatLog('You', question);
        textarea.value = '';
        chrome.runtime.sendMessage({
          action: 'chat',
          data: {
            question,
            platform: this.platform,
            recipient: this.getRecipient(),
            current_url: window.location.href
          }
        }, (response) => {
          if (response?.success) {
            this.appendChatLog('Assistant', response.data.answer);
          } else {
            this.appendChatLog('Assistant', `Error: ${response?.error || 'Unable to chat right now.'}`);
          }
        });
      } else if (action === 'summarizer-send') {
        const textarea = sidebar.querySelector('.ai-composer-summarizer-input');
        const question = textarea.value.trim();
        if (!question) return;
        this.appendSummarizerLog('You', question);
        textarea.value = '';
        chrome.runtime.sendMessage({
          action: 'chat',
          data: {
            question,
            current_url: window.location.href,
            session_id: 'summarizer'  // Separate session for summarizer
          }
        }, (response) => {
          if (response?.success) {
            this.appendSummarizerLog('Assistant', response.data.answer);
          } else {
            this.appendSummarizerLog('Assistant', `Error: ${response?.error || 'Unable to chat right now.'}`);
          }
        });
      }
    });

    wrapper.appendChild(fab);
    wrapper.appendChild(sidebar);
    document.body.appendChild(wrapper);

    this.sidebarWrapper = wrapper;
    this.sidebar = sidebar;
    this.chatContainer = sidebar.querySelector('.ai-composer-chat-container');
  }

  appendChatLog(role, text) {
    if (!this.sidebar) return;
    this.chatContainer?.classList.remove('hidden');
    const log = this.sidebar.querySelector('.ai-composer-chat-log');
    const entry = document.createElement('div');
    entry.className = `ai-composer-chat-entry ai-composer-chat-${role.toLowerCase()}`;
    
    const messageText = document.createElement('div');
    messageText.className = 'ai-composer-message-text';
    messageText.innerHTML = `<strong>${role}:</strong> ${text}`;
    entry.appendChild(messageText);
    
    // Add copy button for Assistant responses
    if (role.toLowerCase() === 'assistant') {
      const copyBtn = document.createElement('button');
      copyBtn.className = 'ai-composer-copy-btn';
      copyBtn.textContent = 'Copy';
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(text).then(() => {
          copyBtn.textContent = '✓ Copied';
          copyBtn.classList.add('copied');
          setTimeout(() => {
            copyBtn.textContent = 'Copy';
            copyBtn.classList.remove('copied');
          }, 2000);
        }).catch(err => {
          console.error('Failed to copy:', err);
          copyBtn.textContent = '✗ Failed';
          setTimeout(() => {
            copyBtn.textContent = 'Copy';
          }, 2000);
        });
      });
      entry.appendChild(copyBtn);
    }
    
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
  }

  observeSendEvents() {
    if (this.platform === 'linkedin') {
      document.addEventListener('click', (event) => {
        const sendButton = event.target.closest('button.msg-form__send-button, button[data-control-name="send"]');
        if (sendButton) {
          const message = (this.latestDraft || '').trim();
          if (message) {
            const recipient = this.getRecipient();
            this.storeMessage(recipient, message, true);
            this.updateStats('conversationCount');
            this.latestDraft = '';
          }
        }
      }, true);
    } else if (this.platform === 'gmail') {
      document.addEventListener('click', (event) => {
        const sendButton = event.target.closest('div[role="button"][data-tooltip*="Send"], div[role="button"][aria-label^="Send"]');
        if (sendButton) {
          const message = (this.latestDraft || '').trim();
          if (message) {
            const recipient = this.getRecipient();
            this.storeMessage(recipient, message, true);
            this.updateStats('conversationCount');
            this.latestDraft = '';
          }
        }
      }, true);
    }
  }

  captureProfile() {
    const profileUrl = window.location.href;
    
    // If LinkedIn, scrape profile data from DOM
    let profileData = {};
    if (this.platform === 'linkedin') {
      profileData = this.scrapeLinkedInProfile();
      console.log('📊 Scraped LinkedIn profile data:', profileData);
    }
    
    chrome.runtime.sendMessage({
      action: 'storeProfile',
      data: {
        platform: this.platform,
        profile_url: profileUrl,
        profile_data: profileData  // Send scraped data
      }
    }, (response) => {
      if (response?.success) {
        const profile = response.data?.profile || {};
        const heading = profile.name || profileData.name || profileUrl;
        const summary = profile.summary || profileData.headline || '';
        this.appendChatLog('System', `Captured profile for ${heading}`);
        const message = `This is my ${this.platform} connection - ${heading}. ${summary}`;
        this.storeMessage(heading, message, true);
        this.updateStats('conversationCount');
      } else {
        console.warn('Failed to store profile', response?.error);
        this.appendChatLog('System', `Failed to capture profile: ${response?.error || 'Unknown error'}`);
      }
    });
  }
  
  scrapeLinkedInProfile() {
    /**
     * Scrape LinkedIn profile data from the current page DOM
     * This works because the user is already logged in and viewing the page
     */
    const data = {};
    
    try {
      // Name
      const nameElement = document.querySelector('h1.text-heading-xlarge, h1.inline.t-24');
      if (nameElement) {
        data.name = nameElement.textContent.trim();
      }
      
      // Headline
      const headlineElement = document.querySelector('div.text-body-medium, div.pv-text-details__left-panel div.text-body-medium');
      if (headlineElement) {
        data.headline = headlineElement.textContent.trim();
      }
      
      // Location
      const locationElement = document.querySelector('span.text-body-small.inline.t-black--light.break-words');
      if (locationElement) {
        data.location = locationElement.textContent.trim();
      }
      
      // About/Summary
      const aboutSection = document.querySelector('section[data-section="summary"], div#about');
      if (aboutSection) {
        const aboutText = aboutSection.querySelector('div.display-flex.ph5.pv3 span[aria-hidden="true"], div.pv-shared-text-with-see-more span[aria-hidden="true"]');
        if (aboutText) {
          data.about = aboutText.textContent.trim();
        }
      }
      
      // Experience
      const experienceSection = document.querySelector('section[data-section="experience"], div#experience');
      if (experienceSection) {
        const experiences = [];
        const expItems = experienceSection.querySelectorAll('li.artdeco-list__item');
        expItems.forEach((item, index) => {
          if (index < 5) {  // Limit to first 5 experiences
            const title = item.querySelector('div.display-flex.align-items-center span[aria-hidden="true"]');
            const company = item.querySelector('span.t-14.t-normal span[aria-hidden="true"]');
            const duration = item.querySelector('span.t-14.t-normal.t-black--light span[aria-hidden="true"]');
            
            if (title) {
              experiences.push({
                title: title.textContent.trim(),
                company: company ? company.textContent.trim() : '',
                duration: duration ? duration.textContent.trim() : ''
              });
            }
          }
        });
        if (experiences.length > 0) {
          data.experience = experiences;
        }
      }
      
      // Education
      const educationSection = document.querySelector('section[data-section="education"], div#education');
      if (educationSection) {
        const education = [];
        const eduItems = educationSection.querySelectorAll('li.artdeco-list__item');
        eduItems.forEach((item, index) => {
          if (index < 3) {  // Limit to first 3 education entries
            const school = item.querySelector('div.display-flex.align-items-center span[aria-hidden="true"]');
            const degree = item.querySelector('span.t-14.t-normal span[aria-hidden="true"]');
            const years = item.querySelector('span.t-14.t-normal.t-black--light span[aria-hidden="true"]');
            
            if (school) {
              education.push({
                school: school.textContent.trim(),
                degree: degree ? degree.textContent.trim() : '',
                years: years ? years.textContent.trim() : ''
              });
            }
          }
        });
        if (education.length > 0) {
          data.education = education;
        }
      }
      
      // Skills
      const skillsSection = document.querySelector('section[data-section="skills"], div#skills');
      if (skillsSection) {
        const skills = [];
        const skillItems = skillsSection.querySelectorAll('div.display-flex.align-items-center span[aria-hidden="true"]');
        skillItems.forEach((item, index) => {
          if (index < 10) {  // Limit to first 10 skills
            const skillText = item.textContent.trim();
            if (skillText && !skills.includes(skillText)) {
              skills.push(skillText);
            }
          }
        });
        if (skills.length > 0) {
          data.skills = skills;
        }
      }
      
      console.log('✓ Scraped LinkedIn profile:', data);
    } catch (error) {
      console.error('Error scraping LinkedIn profile:', error);
    }
    
    return data;
  }

  enterSummarizerMode() {
    const currentUrl = window.location.href;
    const pageTitle = document.title;
    
    // Hide main actions and chat
    const actionsContainer = this.sidebar.querySelector('.ai-composer-actions');
    const chatContainer = this.sidebar.querySelector('.ai-composer-chat-container');
    const summarizerContainer = this.sidebar.querySelector('.ai-composer-summarizer-container');
    
    if (actionsContainer) actionsContainer.classList.add('hidden');
    if (chatContainer) chatContainer.classList.add('hidden');
    if (summarizerContainer) summarizerContainer.classList.remove('hidden');
    
    // Auto-scrape and summarize the page
    this.appendSummarizerLog('System', `📄 Scraping and summarizing: ${pageTitle}...`);
    
    chrome.runtime.sendMessage({
      action: 'summarize',
      data: {
        url: currentUrl,
        title: pageTitle
      }
    }, (response) => {
      if (response?.success) {
        const data = response.data || {};
        this.appendSummarizerLog('System', `✓ Page "${data.title}" analyzed!`);
        
        // Display the automatic summary
        if (data.summary) {
          this.appendSummarizerLog('Assistant', data.summary);
        }
        
        this.appendSummarizerLog('System', `💬 Ask me anything about this page!`);
        
        // Focus the input
        const textarea = this.sidebar.querySelector('.ai-composer-summarizer-input');
        textarea?.focus();
      } else {
        console.warn('Failed to summarize page', response?.error);
        this.appendSummarizerLog('System', `❌ Failed to summarize: ${response?.error || 'Unknown error'}`);
      }
    });
  }

  exitSummarizerMode() {
    // Show main actions, hide summarizer
    const actionsContainer = this.sidebar.querySelector('.ai-composer-actions');
    const summarizerContainer = this.sidebar.querySelector('.ai-composer-summarizer-container');
    
    if (actionsContainer) actionsContainer.classList.remove('hidden');
    if (summarizerContainer) summarizerContainer.classList.add('hidden');
  }

  appendSummarizerLog(role, message) {
    const logContainer = this.sidebar?.querySelector('.ai-composer-summarizer-log');
    if (!logContainer) return;
    
    const entry = document.createElement('div');
    entry.className = `ai-composer-chat-entry ai-composer-chat-${role.toLowerCase()}`;
    
    const messageText = document.createElement('div');
    messageText.className = 'ai-composer-message-text';
    messageText.innerHTML = `<strong>${role}:</strong> ${message}`;
    entry.appendChild(messageText);
    
    // Add copy button for Assistant responses
    if (role.toLowerCase() === 'assistant') {
      const copyBtn = document.createElement('button');
      copyBtn.className = 'ai-composer-copy-btn';
      copyBtn.textContent = 'Copy';
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(message).then(() => {
          copyBtn.textContent = '✓ Copied';
          copyBtn.classList.add('copied');
          setTimeout(() => {
            copyBtn.textContent = 'Copy';
            copyBtn.classList.remove('copied');
          }, 2000);
        }).catch(err => {
          console.error('Failed to copy:', err);
          copyBtn.textContent = '✗ Failed';
          setTimeout(() => {
            copyBtn.textContent = 'Copy';
          }, 2000);
        });
      });
      entry.appendChild(copyBtn);
    }
    
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
  }

  makeDraggable(wrapper, fab) {
    if (!wrapper || !fab) return;

    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;
    let startX = 0;
    let startY = 0;
    
    // Store reference to moved state so click handler can access it
    this._wasDragged = false;

    const onMouseMove = (event) => {
      if (!isDragging) return;
      
      event.preventDefault();
      
      const deltaX = Math.abs(event.clientX - startX);
      const deltaY = Math.abs(event.clientY - startY);
      
      // Only consider it a drag if moved more than 5px
      if (deltaX > 5 || deltaY > 5) {
        this._wasDragged = true;
        const newX = event.clientX - offsetX;
        const newY = event.clientY - offsetY;
        
        // Keep within viewport bounds
        const maxX = window.innerWidth - wrapper.offsetWidth;
        const maxY = window.innerHeight - wrapper.offsetHeight;
        
        wrapper.style.left = `${Math.max(0, Math.min(newX, maxX))}px`;
        wrapper.style.top = `${Math.max(0, Math.min(newY, maxY))}px`;
        wrapper.style.right = 'auto';
        wrapper.style.bottom = 'auto';
      }
    };

    const stopDrag = () => {
      if (!isDragging) return;
      isDragging = false;
      fab.style.cursor = 'grab';
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', stopDrag);
      
      // Reset drag state after a short delay
      setTimeout(() => {
        this._wasDragged = false;
      }, 150);
    };

    fab.style.cursor = 'grab';
    fab.style.userSelect = 'none';
    
    fab.addEventListener('mousedown', (event) => {
      if (event.button !== 0) return; // Only left click
      
      event.preventDefault();
      event.stopPropagation();
      
      const rect = wrapper.getBoundingClientRect();
      isDragging = true;
      this._wasDragged = false;
      startX = event.clientX;
      startY = event.clientY;
      offsetX = event.clientX - rect.left;
      offsetY = event.clientY - rect.top;

      fab.style.cursor = 'grabbing';
      
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', stopDrag);
    });
    
    // Prevent text selection during drag
    fab.addEventListener('dragstart', (e) => e.preventDefault());
  }
}

// Initialize when script loads
const composer = new MessageComposer();

