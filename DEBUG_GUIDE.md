# Debug Guide - AI Message Composer

Complete guide to debugging the extension with detailed logs at every step.

## 🔍 How to View Debug Logs

### 1. Content Script Logs (LinkedIn/Gmail page)
1. Open LinkedIn or Gmail
2. Press **F12** to open Chrome DevTools
3. Go to **Console** tab
4. Click the "✨ AI Rewrite" button
5. Watch the logs appear in real-time

### 2. Background Script Logs (Extension background)
1. Go to `chrome://extensions/`
2. Find "AI Message Composer"
3. Click **"Service worker"** link
4. A new DevTools window opens
5. Go to **Console** tab
6. Click the "✨ AI Rewrite" button on LinkedIn/Gmail
7. Watch the background logs

### 3. Backend Server Logs (Python terminal)
1. Look at the terminal where you ran `python main.py`
2. Logs appear automatically when requests are received
3. Shows detailed timing for each step

## 📊 Complete Log Flow

When you click "✨ AI Rewrite", you'll see logs in **3 places**:

### Content Script Console (F12 on LinkedIn/Gmail)
```
════════════════════════════════════════════════════════════
🚀 STEP 1: Rewrite button clicked
════════════════════════════════════════════════════════════
   → Using active element as input
✓ Step 1 complete: 0.50ms

📝 STEP 2: Getting text from textbox...
   → Input text: hey can we meet tomorrow?
   → Text length: 25
✓ Step 2 complete: 1.20ms
   → Button updated to loading state

🔍 STEP 3: Scraping context (max 1 second)...
   → Platform: linkedin
   → Recipient: John Doe
   → Context messages found: 2
   → First message: Hi! How are you doing?...
✓ Step 3 complete: 45.30ms

📤 STEP 4: Sending to background script → API → LLM...
   → Platform: linkedin
   → Recipient: John Doe
   → User input length: 25
   → Context messages: 2
   → Sending message to background script...
   → Response received from background
   → Response success: true
✓ Step 4 complete: 3245.67ms

✅ STEP 5: Got rewritten text from LLM
   → Original length: 25
   → Rewritten length: 156
   → Rewritten text: Hello John, I hope this message finds you well. Would you be available for a meeting tomorrow...
✓ Step 5 complete: 2.10ms

🔄 STEP 6: Replacing text in textbox...
   → Input field type: contentEditable
✅ Text updated in input field
✓ Step 6 complete: 8.40ms

🎉 STEP 7: Showing success feedback
   → Storing conversation in background
   → Button updated to "Done!"
   → Button restored to original state

════════════════════════════════════════════════════════════
✅ REWRITE COMPLETE
   Total time: 3303.27ms (3.30s)
════════════════════════════════════════════════════════════

⏱️  Total flow time: 3303.27ms
```

### Background Script Console (Service Worker)
```
────────────────────────────────────────────────────────────
📡 BACKGROUND: Received rewrite request from content script
────────────────────────────────────────────────────────────
   → Platform: linkedin
   → Recipient: John Doe
   → User input length: 25
   → Context messages: 2
   → API URL: http://localhost:8000

🌐 BACKGROUND: Calling backend API...
   → Endpoint: http://localhost:8000/api/rewrite
   → Request body size: 342 bytes
   → Fetch completed in: 3234.56ms
   → Response status: 200 OK
   → JSON parsed in: 1.23ms
   → Rewritten message length: 156
   → Context used: true

✅ BACKGROUND: Request complete
   → Total background time: 3236.89ms
   → Sending response back to content script
────────────────────────────────────────────────────────────
```

### Backend Server Terminal
```
============================================================
📝 REWRITE REQUEST RECEIVED
   Platform: linkedin
   Recipient: John Doe
   User Input: hey can we meet tomorrow?
   Tone: professional
   Model: claude-3-haiku-20240307
🔍 Step 1: Querying Neo4j for conversation history...
   ✓ Neo4j query completed in 0.03s
   ✓ Found 2 past messages
📋 Step 2: Building context string...
   ✓ Context built in 0.01s
   ✓ Context length: 145 characters
🤖 Step 3: Calling LLM (claude-3-haiku-20240307)...
   This may take 2-8 seconds depending on model...
   → Prompt being sent to LLM:
   --------------------------------------------------
   Rewrite the following message in LinkedIn style (professional networking tone).

   Previous conversation context:
   John Doe: Hi! How are you doing?
   You: I'm doing great, thanks for asking!

   Original message:
   hey can we meet tomorrow?

   Rewritten message:
   --------------------------------------------------
   → Sending request to Anthropic API (model: claude-3-haiku-20240307)...
   → Prompt length: 234 characters
   → API call completed in 2.87s
   → Response length: 156 characters
   → Total LLM processing time: 2.89s
   ✓ LLM response received in 2.89s
   ✓ Rewritten message length: 156 characters
✅ REQUEST COMPLETED
   Total time: 2.93s
   Breakdown: Neo4j=0.03s, Context=0.01s, LLM=2.89s
============================================================
```

## 🐛 Common Issues and What to Look For

### Issue 1: Button Click Does Nothing
**Check Content Script Console:**
- Look for: `❌ No valid message input found`
- **Fix:** The input field wasn't detected. Check if LinkedIn/Gmail updated their DOM structure.

### Issue 2: "Please write a message first!"
**Check Content Script Console:**
- Look for: `❌ No text in input field`
- **Fix:** Make sure you typed text in the message box before clicking the button.

### Issue 3: Slow Response (>10 seconds)
**Check all three logs to find bottleneck:**

**If Content Script Step 3 is slow (>1s):**
- Context scraping is taking too long
- **Fix:** Simplify the DOM queries or reduce context limit

**If Background Script fetch time is slow (>5s):**
- Network issue or backend is slow
- Check backend server logs

**If Backend Server LLM step is slow (>8s):**
- LLM API is slow
- **Fix:** Use faster model (claude-3-haiku instead of claude-3-sonnet)

### Issue 4: Text Doesn't Replace in Textbox
**Check Content Script Console:**
- Look for Step 6 logs
- Check: `→ Input field type: contentEditable` or `TEXTAREA`
- **Fix:** LinkedIn/Gmail might have changed their input field structure

### Issue 5: Backend Connection Failed
**Check Background Script Console:**
- Look for: `❌ API error response`
- Check: `→ Response status: 500` or connection error
- **Fix:** 
  - Ensure backend server is running
  - Check `http://localhost:8000/health` in browser
  - Verify Neo4j password is correct

### Issue 6: LLM API Error
**Check Backend Server Terminal:**
- Look for: `❌ ERROR` or `Anthropic API error`
- **Fix:**
  - Check your API key in `.env` file
  - Verify you have API credits
  - Try a different model

## 📈 Performance Benchmarks

**Target times:**
- Step 1 (Button click): < 1ms
- Step 2 (Get text): < 2ms
- Step 3 (Scrape context): < 100ms (timeout at 1000ms)
- Step 4 (API call): 2000-5000ms (depends on LLM)
- Step 5 (Get response): < 5ms
- Step 6 (Replace text): < 10ms
- Step 7 (Feedback): < 5ms

**Total expected time: 2-6 seconds**

If any step is significantly slower, investigate that specific step.

## 🔧 Advanced Debugging

### Enable Verbose Logging
Already enabled! All logs are detailed.

### Check Network Requests
1. Open DevTools (F12)
2. Go to **Network** tab
3. Filter by "rewrite"
4. Click the request
5. Check:
   - Request payload
   - Response data
   - Timing breakdown

### Check Extension Storage
```javascript
// Run in console (F12)
chrome.storage.sync.get(null, (data) => console.log(data));
chrome.storage.local.get(null, (data) => console.log(data));
```

### Test Backend Directly
```bash
curl -X POST http://localhost:8000/api/rewrite \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "user_input": "hey lets meet",
    "conversation_context": [],
    "recipient": "Test User",
    "tone": "professional"
  }'
```

## 📝 Reporting Issues

When reporting issues, include:

1. **Content Script logs** (copy from F12 console)
2. **Background Script logs** (copy from service worker console)
3. **Backend Server logs** (copy from terminal)
4. **Steps to reproduce**
5. **Expected vs actual behavior**
6. **Browser version**
7. **Platform** (LinkedIn or Gmail)

## 🎯 Quick Troubleshooting Checklist

- [ ] Backend server is running (`python main.py`)
- [ ] Neo4j database is running (check Neo4j Desktop)
- [ ] Extension is loaded in Chrome (`chrome://extensions/`)
- [ ] Extension has correct permissions
- [ ] API key is set in `.env` file
- [ ] You're on LinkedIn or Gmail page
- [ ] You typed text in the message box
- [ ] You clicked the "✨ AI Rewrite" button
- [ ] Check all 3 console logs for errors

## 🚀 Next Steps

1. **Reload extension** after code changes
2. **Restart server** after changing `.env` or Python code
3. **Clear console** before each test for clean logs
4. **Test on both** LinkedIn and Gmail
5. **Check timing** for each step to identify bottlenecks

---

**With these detailed logs, you can pinpoint exactly where any issue occurs!**

