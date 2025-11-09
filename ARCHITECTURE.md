# AI Message Composer - Architecture

Detailed architecture documentation for the AI Message Composer system.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              LinkedIn / Gmail Web Page                     │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Message Input Field                                 │  │ │
│  │  │  [Type your message here...]                         │  │ │
│  │  │                                    [✨ AI Rewrite]   │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           Chrome Extension (MV3)                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   Content    │  │  Background  │  │    Popup     │    │ │
│  │  │   Script     │◄─┤   Service    │◄─┤      UI      │    │ │
│  │  │              │  │   Worker     │  │              │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP/REST
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      FastAPI Backend Server                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    API Endpoints                           │ │
│  │  • POST /api/rewrite                                       │ │
│  │  • POST /api/store-conversation                            │ │
│  │  • GET  /api/conversation-history/{recipient}              │ │
│  │  • GET  /health                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │  Neo4j Service   │              │   LLM Service    │         │
│  │  • Store msgs    │              │  • Rewrite msgs  │         │
│  │  • Retrieve ctx  │              │  • Format output │         │
│  │  • Graph queries │              │  • Tone control  │         │
│  └──────────────────┘              └──────────────────┘         │
└───────────┬──────────────────────────────────┬─────────────────┘
            │                                  │
            │                                  │
┌───────────▼──────────┐          ┌───────────▼──────────┐
│   Neo4j Database     │          │   LLM Provider       │
│   • User nodes       │          │   • OpenAI GPT       │
│   • Message nodes    │          │   • Anthropic Claude │
│   • Relationships    │          │                      │
│   • Graph storage    │          │                      │
└──────────────────────┘          └──────────────────────┘
```

## Component Details

### 1. Chrome Extension Layer

#### Content Script (`content.js`)
**Responsibility:** DOM interaction and message field detection

**Key Functions:**
- `detectPlatform()` - Identifies LinkedIn vs Gmail
- `findMessageInputs()` - Locates message input fields
- `scrapeConversationContext()` - Extracts current conversation
- `handleRewrite()` - Manages rewrite workflow
- `attachToInput()` - Injects AI button into page

**Data Flow:**
```
Page Load → Detect Platform → Find Inputs → Attach Buttons
User Types → Click Button → Scrape Context → Send to Background
```

#### Background Service Worker (`background.js`)
**Responsibility:** API communication and message routing

**Key Functions:**
- `handleRewriteMessage()` - Calls rewrite API
- `handleStoreConversation()` - Stores messages
- Message passing between content script and backend

**Data Flow:**
```
Content Script → Message → Background → HTTP Request → Backend
Backend Response → Background → Message → Content Script
```

#### Popup UI (`popup.html/js`)
**Responsibility:** Status display and quick actions

**Features:**
- Connection status indicator
- Message/conversation statistics
- Test connection button
- Settings link

#### Options Page (`options.html/js`)
**Responsibility:** User configuration

**Settings:**
- Backend API URL
- LLM model selection
- Default tone preference
- Auto-store toggle

### 2. Backend API Layer

#### FastAPI Application (`main.py`)
**Responsibility:** HTTP API and request routing

**Endpoints:**

```python
GET  /health
     → Returns: server status, Neo4j connection, LLM availability

POST /api/rewrite
     → Input: platform, user_input, context, recipient, tone
     → Process: Retrieve RAG context → Call LLM → Format response
     → Output: rewritten_message, original, context_used

POST /api/store-conversation
     → Input: platform, recipient, message, is_outgoing, timestamp
     → Process: Store in Neo4j graph
     → Output: success status

GET  /api/conversation-history/{recipient}
     → Input: recipient, platform, limit
     → Process: Query Neo4j for messages
     → Output: list of messages
```

**Middleware:**
- CORS for Chrome extension
- Error handling
- Request validation (Pydantic)

### 3. Service Layer

#### Neo4j Service (`neo4j_service.py`)
**Responsibility:** Graph database operations

**Graph Schema:**
```cypher
// Nodes
(User {id, platform, created_at, last_interaction})
(Message {id, text, is_outgoing, timestamp, platform})

// Relationships
(Message)-[:SENT_TO]->(User)  // Outgoing
(User)-[:SENT]->(Message)     // Incoming
```

**Key Operations:**
```python
store_message()
  → Create User node (if not exists)
  → Create Message node
  → Create relationship
  → Update user metadata

get_conversation_history()
  → Match User by recipient + platform
  → Find related Messages
  → Order by timestamp
  → Return chronologically

get_user_stats()
  → Count total messages
  → Count outgoing/incoming
  → Get last interaction time
```

#### LLM Service (`llm_service.py`)
**Responsibility:** AI model integration

**Supported Models:**
- OpenAI: GPT-4, GPT-3.5-turbo
- Anthropic: Claude 3 Opus, Sonnet, Haiku

**Prompt Structure:**
```
System: You are a professional writing assistant
Context: [Platform, Tone, Conversation History]
User Input: [Original message]
Instructions: [Rewrite guidelines]
Output: [Professional rewritten message]
```

**Key Functions:**
```python
rewrite_message()
  → Build prompt with context
  → Route to appropriate provider
  → Call LLM API
  → Extract and return response

_build_prompt()
  → Platform-specific guidance
  → Tone-specific instructions
  → Context integration
  → Formatting rules
```

### 4. Data Layer

#### Neo4j Database
**Responsibility:** Persistent graph storage

**Indexes:**
```cypher
CREATE CONSTRAINT user_id FOR (u:User) REQUIRE u.id IS UNIQUE
CREATE CONSTRAINT message_id FOR (m:Message) REQUIRE m.id IS UNIQUE
CREATE INDEX user_platform FOR (u:User) ON (u.platform)
CREATE INDEX message_timestamp FOR (m:Message) ON (m.timestamp)
```

**Query Patterns:**
```cypher
// Store message
MERGE (u:User {id: $recipient, platform: $platform})
CREATE (m:Message {...})
CREATE (m)-[:SENT_TO]->(u)

// Retrieve history
MATCH (u:User {id: $recipient})-[r]-(m:Message)
RETURN m ORDER BY m.timestamp DESC LIMIT 10

// Get stats
MATCH (u:User {id: $recipient})-[r]-(m:Message)
RETURN count(m), max(m.timestamp)
```

## Data Flow Diagrams

### Message Rewrite Flow

```
1. User Types Message
   ↓
2. Content Script Detects Input
   ↓
3. User Clicks "✨ AI Rewrite"
   ↓
4. Content Script:
   - Scrapes current conversation
   - Identifies recipient
   - Gets user input
   ↓
5. Send to Background Worker
   ↓
6. Background Worker → HTTP POST /api/rewrite
   ↓
7. Backend FastAPI:
   - Validates request
   - Calls Neo4j Service
   ↓
8. Neo4j Service:
   - Queries conversation history
   - Returns past messages
   ↓
9. Backend builds context:
   - Current conversation
   - Past conversations (RAG)
   - Platform info
   - Tone preference
   ↓
10. LLM Service:
    - Builds prompt
    - Calls OpenAI/Anthropic
    - Gets rewritten message
    ↓
11. Backend returns response
    ↓
12. Background Worker receives response
    ↓
13. Content Script:
    - Replaces text in input field
    - Shows success
    ↓
14. Optional: Store conversation in Neo4j
```

### Conversation Storage Flow

```
1. Message Sent/Received
   ↓
2. Content Script (if auto-store enabled):
   - Captures message
   - Identifies recipient
   - Gets timestamp
   ↓
3. Send to Background Worker
   ↓
4. Background Worker → HTTP POST /api/store-conversation
   ↓
5. Backend FastAPI:
   - Validates request
   - Calls Neo4j Service
   ↓
6. Neo4j Service:
   - MERGE User node
   - CREATE Message node
   - CREATE relationship
   - Update user metadata
   ↓
7. Backend returns success
   ↓
8. Update statistics in extension
```

## Technology Stack Details

### Frontend Technologies

**Chrome Extension (Manifest V3)**
- Service Workers (replaces background pages)
- Content Scripts with isolated world
- Chrome Storage API for settings
- Chrome Runtime messaging
- Chrome Tabs API

**JavaScript ES6+**
- Async/await patterns
- Promises for async operations
- DOM manipulation
- Event listeners
- Fetch API for HTTP

### Backend Technologies

**FastAPI Framework**
- Async request handling
- Pydantic data validation
- Automatic OpenAPI docs
- CORS middleware
- Dependency injection

**Python 3.9+**
- Type hints
- Async/await
- Context managers
- Decorators

### Database Technologies

**Neo4j Graph Database**
- Cypher query language
- ACID transactions
- Graph algorithms
- Indexes and constraints
- Bolt protocol

### AI/ML Technologies

**OpenAI API**
- GPT-4 (175B+ parameters)
- GPT-3.5-turbo (optimized)
- Chat completions API
- Token-based pricing

**Anthropic API**
- Claude 3 Opus (largest)
- Claude 3 Sonnet (balanced)
- Claude 3 Haiku (fastest)
- Messages API

## Security Architecture

### API Key Management
```
Developer Machine:
  .env file (gitignored)
  ↓
Environment Variables
  ↓
Backend reads at startup
  ↓
Never exposed to frontend
```

### Extension Permissions
```json
{
  "permissions": ["activeTab", "storage", "scripting"],
  "host_permissions": [
    "https://www.linkedin.com/*",
    "https://mail.google.com/*"
  ]
}
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev: all origins
    # Production: specific extension ID
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Data Privacy
- Messages stored locally in Neo4j
- No third-party analytics
- User controls data storage
- Can delete conversation history
- API keys stored securely

## Scalability Considerations

### Current Architecture (Single User)
- Local Neo4j instance
- Local FastAPI server
- Single Chrome profile

### Multi-User Scaling
```
Load Balancer
  ↓
FastAPI Instances (3+)
  ↓
Neo4j Cluster (3+ nodes)
  ↓
Shared LLM API pool
```

### Performance Optimizations
- Neo4j indexes on frequent queries
- Async request handling
- Connection pooling
- Response caching (future)
- Rate limiting (future)

## Error Handling

### Extension Layer
```javascript
try {
  // API call
} catch (error) {
  // Show user-friendly message
  // Log to console
  // Don't crash extension
}
```

### Backend Layer
```python
try:
  # Process request
except Neo4jException:
  # Log error
  # Return 500 with message
except LLMException:
  # Log error
  # Return 503 with message
```

### Database Layer
```python
with driver.session() as session:
  try:
    session.execute_write(tx_function)
  except Exception:
    # Rollback automatic
    # Raise to caller
```

## Monitoring & Logging

### Extension Logs
- Chrome DevTools Console
- Service Worker logs
- Error tracking

### Backend Logs
- Uvicorn access logs
- Application logs
- Error traces
- API response times

### Database Logs
- Neo4j query logs
- Slow query detection
- Connection pool stats

## Deployment Architecture

### Development
```
Localhost:
  - Neo4j: bolt://localhost:7687
  - Backend: http://localhost:8000
  - Extension: Unpacked
```

### Production (Future)
```
Cloud Infrastructure:
  - Neo4j Aura (managed)
  - FastAPI on AWS/GCP
  - Extension on Chrome Web Store
  - HTTPS with SSL
  - CDN for static assets
```

## Testing Architecture

### Unit Tests
- Python: pytest
- JavaScript: Jest (future)

### Integration Tests
- API endpoint tests
- Neo4j query tests
- LLM mock tests

### E2E Tests
- Selenium for browser automation
- Test on real LinkedIn/Gmail
- Verify complete flow

## Future Architecture Enhancements

### Phase 2
- Redis caching layer
- Message queue (RabbitMQ)
- Webhook support
- Real-time updates

### Phase 3
- Microservices architecture
- Kubernetes deployment
- Multi-region support
- Advanced analytics

---

**Architecture Version:** 1.0
**Last Updated:** 2024
**Status:** Production-ready for single-user deployment

