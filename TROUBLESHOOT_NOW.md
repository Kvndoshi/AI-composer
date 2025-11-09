# 🚨 Button Stuck Loading - Troubleshooting

## Step 1: Check Content Script Console

1. **On LinkedIn/Gmail page, press F12**
2. **Click "Console" tab**
3. **Look for any RED errors**
4. **Take a screenshot and share it**

If you see nothing, the content script isn't loaded.

## Step 2: Check Background Script Console

1. **New tab → chrome://extensions/**
2. **Find "AI Message Composer"**
3. **Click "service worker" (blue text)**
4. **New window opens → Console tab**
5. **Look for errors**

## Step 3: Force Reload Everything

```
1. Close ALL LinkedIn/Gmail tabs
2. Go to chrome://extensions/
3. Click REMOVE on "AI Message Composer"
4. Click "Load unpacked" again
5. Select: C:\Users\kevin\vscode_files\claudehacksextension\extension
6. Open NEW LinkedIn/Gmail tab
7. Try again
```

## Step 4: Check Server Terminal

**Find the terminal window with:**
```
🚀 STARTING AI MESSAGE COMPOSER SERVER
```

If you don't see this window:
1. Close any Python terminal windows
2. Double-click: `START_SERVER.bat`
3. New window should open with server logs

## Step 5: Test Manually

**Open this in browser:**
http://localhost:8000/docs

**Try the API directly:**
1. Click "POST /api/rewrite"
2. Click "Try it out"
3. Paste this:
```json
{
  "platform": "linkedin",
  "user_input": "hey lets meet",
  "conversation_context": [],
  "recipient": "Test User",
  "tone": "professional"
}
```
4. Click "Execute"
5. Check response

## Common Issues

### Issue 1: No logs in F12 Console
**Problem:** Content script not loaded
**Fix:** Reload extension + refresh page

### Issue 2: "service worker" link is inactive
**Problem:** Background script crashed
**Fix:** Reload extension

### Issue 3: Button exists but does nothing
**Problem:** JavaScript error
**Fix:** Check F12 console for red errors

### Issue 4: Button loading forever
**Problem:** API call not completing
**Fix:** Check background script console for network errors

## Quick Test

**In F12 Console, type:**
```javascript
document.querySelector('.ai-composer-button')
```

**Should return:** The button element
**If null:** Button wasn't injected

**Then type:**
```javascript
chrome.runtime.sendMessage({action: 'getSettings'}, console.log)
```

**Should return:** Settings object
**If error:** Extension communication broken

## Emergency Reset

```bash
# 1. Stop server (Ctrl+C in terminal)
# 2. Remove extension from Chrome
# 3. Restart Chrome completely
# 4. Start server: python main.py
# 5. Load extension fresh
# 6. Test on NEW tab
```

---

**What to share with me:**
1. Screenshot of F12 console (any errors?)
2. Screenshot of service worker console (any errors?)
3. Does http://localhost:8000/docs work in browser?

