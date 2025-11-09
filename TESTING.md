# Testing Guide - AI Message Composer

Comprehensive testing procedures for the AI Message Composer extension.

## Pre-Test Checklist

Before testing, ensure:
- [ ] Neo4j database is running
- [ ] Backend server is running on port 8000
- [ ] Chrome extension is installed and enabled
- [ ] Extension settings are configured
- [ ] You have API credits available

## Test Suite

### 1. Backend API Tests

#### 1.1 Health Check Test

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "llm_available": true
}
```

**Pass Criteria:**
- Status code: 200
- All boolean values are `true`

#### 1.2 Message Rewrite Test

```bash
curl -X POST http://localhost:8000/api/rewrite \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "user_input": "hey can we meet tomorrow?",
    "conversation_context": [],
    "recipient": "Test User",
    "tone": "professional"
  }'
```

**Expected Response:**
```json
{
  "rewritten_message": "Hello,\n\nWould you be available for a meeting tomorrow?\n\nBest regards",
  "original_message": "hey can we meet tomorrow?",
  "context_used": false,
  "rag_context": null
}
```

**Pass Criteria:**
- Status code: 200
- `rewritten_message` is more professional than input
- Response time < 5 seconds

#### 1.3 Store Conversation Test

```bash
curl -X POST http://localhost:8000/api/store-conversation \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "recipient": "John Doe",
    "message": "Thanks for connecting!",
    "is_outgoing": true,
    "timestamp": "2024-01-01T10:00:00Z"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Conversation stored"
}
```

**Pass Criteria:**
- Status code: 200
- Message stored in Neo4j

#### 1.4 Retrieve Conversation History Test

```bash
curl "http://localhost:8000/api/conversation-history/John%20Doe?platform=linkedin&limit=10"
```

**Expected Response:**
```json
{
  "recipient": "John Doe",
  "messages": [
    {
      "message": "Thanks for connecting!",
      "is_outgoing": true,
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ]
}
```

**Pass Criteria:**
- Status code: 200
- Returns previously stored message

### 2. Neo4j Database Tests

Open Neo4j Browser at http://localhost:7474 and run these queries:

#### 2.1 Verify Schema

```cypher
CALL db.schema.visualization()
```

**Pass Criteria:**
- Shows `User` and `Message` nodes
- Shows `SENT` and `SENT_TO` relationships

#### 2.2 Count Stored Messages

```cypher
MATCH (m:Message)
RETURN count(m) as total_messages
```

**Pass Criteria:**
- Returns count > 0 after storing messages

#### 2.3 View Conversation Graph

```cypher
MATCH (u:User {id: "John Doe"})-[r]-(m:Message)
RETURN u, r, m
LIMIT 25
```

**Pass Criteria:**
- Shows user node connected to message nodes
- Relationships are correctly labeled

#### 2.4 Test User Stats

```cypher
MATCH (u:User {id: "John Doe"})-[r]-(m:Message)
RETURN u.id as user,
       count(m) as total_messages,
       sum(CASE WHEN m.is_outgoing THEN 1 ELSE 0 END) as sent,
       sum(CASE WHEN NOT m.is_outgoing THEN 1 ELSE 0 END) as received
```

**Pass Criteria:**
- Returns accurate message counts

### 3. Chrome Extension Tests

#### 3.1 Extension Installation Test

1. Go to `chrome://extensions/`
2. Find "AI Message Composer"

**Pass Criteria:**
- Extension is visible
- Status is "Enabled"
- No errors shown

#### 3.2 Popup Test

1. Click extension icon in toolbar
2. Observe popup

**Pass Criteria:**
- Popup opens without errors
- Shows connection status
- Displays message/conversation counts
- "Test Connection" button works

#### 3.3 Settings Page Test

1. Click extension icon
2. Click "Settings"
3. Modify settings
4. Click "Save Settings"

**Pass Criteria:**
- Settings page opens
- All fields are editable
- Save confirmation appears
- Settings persist after reload

#### 3.4 Background Service Worker Test

1. Go to `chrome://extensions/`
2. Click "Service worker" under extension
3. Check console

**Pass Criteria:**
- No errors in console
- Service worker is active

### 4. LinkedIn Integration Tests

#### 4.1 Message Detection Test

1. Go to https://www.linkedin.com/messaging/
2. Select a conversation
3. Click in message input field

**Pass Criteria:**
- "✨ AI Rewrite" button appears
- Button is positioned correctly
- Button is clickable

#### 4.2 Message Rewrite Test

1. Type: "hey wanna connect?"
2. Click "✨ AI Rewrite"
3. Wait for response

**Pass Criteria:**
- Button shows loading state
- Message is replaced with professional version
- Original intent is preserved
- No errors in console

#### 4.3 Context Scraping Test

1. Open a conversation with message history
2. Type a new message
3. Click "✨ AI Rewrite"
4. Check backend logs

**Pass Criteria:**
- Previous messages are scraped
- Context is sent to backend
- Rewritten message considers context

#### 4.4 Recipient Detection Test

1. Open different conversations
2. Use AI rewrite in each
3. Check Neo4j for stored messages

**Pass Criteria:**
- Correct recipient name is captured
- Messages are associated with right user

### 5. Gmail Integration Tests

#### 5.1 Compose Detection Test

1. Go to https://mail.google.com/
2. Click "Compose"
3. Click in message body

**Pass Criteria:**
- "✨ AI Rewrite" button appears
- Button doesn't interfere with Gmail UI

#### 5.2 Email Rewrite Test

1. Type: "hey thanks for the info"
2. Click "✨ AI Rewrite"

**Pass Criteria:**
- Message is rewritten in email format
- Includes appropriate greeting/closing
- Professional tone

#### 5.3 Reply Context Test

1. Open an email thread
2. Click "Reply"
3. Type a message
4. Click "✨ AI Rewrite"

**Pass Criteria:**
- Previous email content is captured
- Reply considers email context
- Maintains conversation thread

### 6. RAG Context Tests

#### 6.1 First Conversation Test

1. Message a new contact (not in database)
2. Use AI rewrite

**Pass Criteria:**
- Works without existing context
- `context_used: false` in response

#### 6.2 Subsequent Conversation Test

1. Store some messages with a contact
2. Write a new message to same contact
3. Use AI rewrite
4. Check response

**Pass Criteria:**
- Previous messages are retrieved
- `context_used: true` in response
- Rewrite references past conversation

#### 6.3 Context Relevance Test

1. Store unrelated messages with different contacts
2. Message a specific contact
3. Use AI rewrite

**Pass Criteria:**
- Only relevant contact's history is used
- No cross-contamination of contexts

### 7. Tone Variation Tests

Test each tone setting:

#### 7.1 Professional Tone
- Input: "hey lets meet"
- Expected: Formal business language

#### 7.2 Friendly Tone
- Input: "thanks for helping"
- Expected: Warm but professional

#### 7.3 Formal Tone
- Input: "can you send the docs"
- Expected: Very formal, respectful

#### 7.4 Casual Tone
- Input: "got it, will do"
- Expected: Relaxed but clear

**Pass Criteria for All:**
- Tone matches selection
- Message is appropriate for platform
- Core meaning preserved

### 8. Error Handling Tests

#### 8.1 Backend Offline Test

1. Stop the backend server
2. Try to use AI rewrite

**Pass Criteria:**
- Shows clear error message
- Extension doesn't crash
- Can retry after server restarts

#### 8.2 Invalid API Key Test

1. Set invalid API key in `.env`
2. Restart server
3. Try to rewrite message

**Pass Criteria:**
- Returns API error message
- Error is logged
- Extension handles gracefully

#### 8.3 Neo4j Offline Test

1. Stop Neo4j database
2. Try to rewrite message

**Pass Criteria:**
- Rewrite still works (without context)
- Error logged for storage failure
- Doesn't block main functionality

#### 8.4 Empty Message Test

1. Click "✨ AI Rewrite" with empty field

**Pass Criteria:**
- Shows "Please write a message first!"
- Doesn't make API call

#### 8.5 Network Timeout Test

1. Simulate slow network
2. Try to rewrite message

**Pass Criteria:**
- Shows loading state
- Eventually times out with error
- Can retry

### 9. Performance Tests

#### 9.1 Response Time Test

Measure time from button click to message replacement:

**Pass Criteria:**
- < 3 seconds for GPT-3.5
- < 5 seconds for GPT-4
- < 4 seconds for Claude

#### 9.2 Concurrent Requests Test

1. Open multiple LinkedIn/Gmail tabs
2. Trigger rewrites simultaneously

**Pass Criteria:**
- All requests complete successfully
- No race conditions
- Correct messages in each tab

#### 9.3 Large Context Test

1. Create conversation with 50+ messages
2. Try to rewrite new message

**Pass Criteria:**
- Handles large context
- Response time < 10 seconds
- Doesn't crash

### 10. Data Integrity Tests

#### 10.1 Message Storage Accuracy

1. Send several messages
2. Query Neo4j directly
3. Compare with actual messages

**Pass Criteria:**
- All messages stored correctly
- Timestamps are accurate
- is_outgoing flag is correct

#### 10.2 Unicode/Emoji Test

1. Type message with emojis: "hey 👋 lets connect 🚀"
2. Rewrite and store

**Pass Criteria:**
- Handles special characters
- Stores correctly in Neo4j
- Retrieves without corruption

#### 10.3 Long Message Test

1. Type 500+ word message
2. Rewrite

**Pass Criteria:**
- Handles long input
- Output is appropriately sized
- Doesn't truncate unexpectedly

## Automated Test Script

Save as `test_api.py`:

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    print("✓ Health check passed")

def test_rewrite():
    data = {
        "platform": "linkedin",
        "user_input": "hey lets meet",
        "conversation_context": [],
        "recipient": "Test User",
        "tone": "professional"
    }
    r = requests.post(f"{BASE_URL}/api/rewrite", json=data)
    assert r.status_code == 200
    assert len(r.json()["rewritten_message"]) > 0
    print("✓ Rewrite test passed")

def test_store():
    data = {
        "platform": "linkedin",
        "recipient": "Test User",
        "message": "Test message",
        "is_outgoing": True,
        "timestamp": "2024-01-01T10:00:00Z"
    }
    r = requests.post(f"{BASE_URL}/api/store-conversation", json=data)
    assert r.status_code == 200
    print("✓ Store test passed")

if __name__ == "__main__":
    test_health()
    test_rewrite()
    test_store()
    print("\n✓ All tests passed!")
```

Run with:
```bash
python test_api.py
```

## Test Results Template

Use this template to document test results:

```
Test Date: [DATE]
Tester: [NAME]
Version: 1.0.0

Backend Tests:
- Health Check: [PASS/FAIL]
- Message Rewrite: [PASS/FAIL]
- Store Conversation: [PASS/FAIL]
- Retrieve History: [PASS/FAIL]

Neo4j Tests:
- Schema Verification: [PASS/FAIL]
- Data Storage: [PASS/FAIL]
- Query Performance: [PASS/FAIL]

Extension Tests:
- Installation: [PASS/FAIL]
- Popup UI: [PASS/FAIL]
- Settings: [PASS/FAIL]

LinkedIn Tests:
- Detection: [PASS/FAIL]
- Rewrite: [PASS/FAIL]
- Context Scraping: [PASS/FAIL]

Gmail Tests:
- Detection: [PASS/FAIL]
- Rewrite: [PASS/FAIL]
- Reply Context: [PASS/FAIL]

Notes:
[Any issues or observations]
```

## Continuous Testing

For ongoing development:

1. **Run health check** before each testing session
2. **Test after code changes** to catch regressions
3. **Monitor logs** during testing for warnings
4. **Check Neo4j data** periodically for integrity
5. **Test on real accounts** (with permission) for realistic scenarios

## Known Issues

Document any known issues here:

- [ ] Issue 1: Description
- [ ] Issue 2: Description

---

**Testing Complete?** If all tests pass, the system is ready for use! 🎉

