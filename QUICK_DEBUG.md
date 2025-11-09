# Quick Debug Reference

## 🎯 Where to Look for Logs

| Location | How to Access | What It Shows |
|----------|---------------|---------------|
| **Content Script** | F12 on LinkedIn/Gmail page → Console | Button clicks, text extraction, DOM operations |
| **Background Script** | chrome://extensions/ → Service worker → Console | API calls, message passing |
| **Backend Server** | Terminal where `python main.py` runs | Neo4j queries, LLM API calls, timing |

## ⚡ Quick Test

1. **Start server:** `python main.py`
2. **Open LinkedIn** or Gmail
3. **Open Console:** Press F12
4. **Type message:** "hey can we meet tomorrow?"
5. **Click:** ✨ AI Rewrite button
6. **Watch logs** in all 3 places

## 📊 Expected Log Flow

```
CONTENT SCRIPT (F12)
  ↓ STEP 1: Button clicked (< 1ms)
  ↓ STEP 2: Get text (< 2ms)
  ↓ STEP 3: Scrape context (< 100ms)
  ↓ STEP 4: Send to background (2-5 seconds)
        ↓
        BACKGROUND SCRIPT (Service Worker)
          ↓ Receive request
          ↓ Call API (2-5 seconds)
                ↓
                BACKEND SERVER (Terminal)
                  ↓ Neo4j query (< 0.1s)
                  ↓ Build context (< 0.1s)
                  ↓ Call LLM (2-5s)
                  ↓ Return response
                ↑
          ↓ Parse response
          ↓ Send back to content
        ↑
  ↓ STEP 5: Got response (< 5ms)
  ↓ STEP 6: Replace text (< 10ms)
  ↓ STEP 7: Show feedback (< 5ms)
  ✅ DONE (Total: 2-6 seconds)
```

## 🐛 If Something's Wrong

### Text doesn't replace?
→ Check **STEP 6** in content script console
→ Look for "Input field type"

### Takes too long?
→ Check **STEP 4** timing
→ Check **backend server** LLM step timing

### Error message?
→ Check **background script** console for API errors
→ Check **backend server** terminal for Python errors

### Button doesn't work?
→ Check **STEP 1** in content script console
→ Reload extension: chrome://extensions/

## 🔧 Quick Fixes

| Problem | Fix |
|---------|-----|
| Backend not connected | Start server: `python main.py` |
| Neo4j error | Check password in `.env`, restart Neo4j |
| API key error | Add key to `.env` file |
| Extension not loading | Reload in chrome://extensions/ |
| Button not appearing | Refresh LinkedIn/Gmail page |
| Slow responses | Use `claude-3-haiku` model |

## 📝 Timing Targets

- Button click → Text extracted: **< 5ms**
- Context scraping: **< 100ms**
- API call (total): **2-5 seconds**
  - Neo4j: **< 0.1s**
  - LLM: **2-5s**
- Text replacement: **< 10ms**

**Total: 2-6 seconds** ⏱️

## 🚨 Common Errors

### "No valid message input found"
- You're not in a message field
- Click in the LinkedIn/Gmail message box first

### "Please write a message first!"
- The text box is empty
- Type something before clicking the button

### "Backend not connected"
- Server isn't running
- Run: `python main.py`

### "API request failed"
- Check server terminal for errors
- Visit: http://localhost:8000/health

### "Anthropic API error"
- Check API key in `.env`
- Verify you have credits

## ✅ Success Indicators

In **Content Script Console:**
```
✅ REWRITE COMPLETE
   Total time: 3.30s
```

In **Background Script Console:**
```
✅ BACKGROUND: Request complete
   → Total background time: 3236.89ms
```

In **Backend Server Terminal:**
```
✅ REQUEST COMPLETED
   Total time: 2.93s
```

Button shows: **✓ Done!**

---

**For detailed debugging, see DEBUG_GUIDE.md**

