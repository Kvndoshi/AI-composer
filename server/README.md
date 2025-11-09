# AI Message Composer - Backend Server

FastAPI backend service that handles message rewriting with RAG using Neo4j for conversation context storage.

## Features

- 🤖 AI-powered message rewriting using OpenAI or Anthropic
- 📊 Neo4j graph database for conversation history
- 🔍 RAG (Retrieval Augmented Generation) for context-aware rewrites
- 🚀 Fast async API with FastAPI
- 🔒 CORS enabled for Chrome extension

## Prerequisites

1. **Python 3.9+**
2. **Neo4j Database**
   - Option A: Local installation from [neo4j.com/download](https://neo4j.com/download/)
   - Option B: Neo4j Desktop (recommended for development)
   - Option C: Neo4j Aura Free Tier (cloud)

3. **LLM API Key** (at least one):
   - OpenAI API key from [platform.openai.com](https://platform.openai.com)
   - Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

## Installation

1. **Install Python dependencies:**

```bash
cd server
pip install -r requirements.txt
```

2. **Set up Neo4j:**

**Option A: Neo4j Desktop (Easiest)**
- Download Neo4j Desktop from https://neo4j.com/download/
- Create a new database
- Set password (remember this!)
- Start the database
- Default connection: `bolt://localhost:7687`

**Option B: Docker**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

**Option C: Neo4j Aura (Free Cloud)**
- Sign up at https://neo4j.com/cloud/aura/
- Create a free instance
- Save the connection URI and credentials

3. **Configure environment variables:**

```bash
# Copy the example file
cp env.example .env

# Edit .env with your credentials
# - Set your Neo4j connection details
# - Add your OpenAI or Anthropic API key
```

Example `.env` file:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

OPENAI_API_KEY=sk-...your-key...
# OR
ANTHROPIC_API_KEY=sk-ant-...your-key...

HOST=0.0.0.0
PORT=8000
DEBUG=True
DEFAULT_MODEL=gpt-4
```

## Running the Server

```bash
# From the server directory
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```
Returns server status and connection health.

### Rewrite Message
```
POST /api/rewrite
```
Rewrites a message using AI with conversation context.

**Request Body:**
```json
{
  "platform": "linkedin",
  "user_input": "hey can we meet tomorrow?",
  "conversation_context": [
    {
      "text": "Hi! How are you?",
      "is_outgoing": false,
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ],
  "recipient": "John Doe",
  "tone": "professional"
}
```

**Response:**
```json
{
  "rewritten_message": "Hello! Would you be available for a meeting tomorrow?",
  "original_message": "hey can we meet tomorrow?",
  "context_used": true,
  "rag_context": "Previous conversation history..."
}
```

### Store Conversation
```
POST /api/store-conversation
```
Stores a message in Neo4j for future context retrieval.

**Request Body:**
```json
{
  "platform": "linkedin",
  "recipient": "John Doe",
  "message": "Thanks for the meeting!",
  "is_outgoing": true,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Get Conversation History
```
GET /api/conversation-history/{recipient}?platform=linkedin&limit=20
```
Retrieves past conversation history with a recipient.

### Delete Conversation History
```
DELETE /api/conversation-history/{recipient}?platform=linkedin
```
Deletes all stored messages for a recipient.

## Testing

Test the API with curl:

```bash
# Health check
curl http://localhost:8000/health

# Test rewrite (requires API key configured)
curl -X POST http://localhost:8000/api/rewrite \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "user_input": "hey wanna connect?",
    "conversation_context": [],
    "recipient": "Test User",
    "tone": "professional"
  }'
```

Or visit the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Neo4j Graph Structure

The system creates the following graph structure:

```
(User {id, platform, created_at, last_interaction})
(Message {id, text, is_outgoing, timestamp, platform})

Relationships:
- (Message)-[:SENT_TO]->(User)  // Outgoing messages
- (User)-[:SENT]->(Message)     // Incoming messages
```

You can explore the graph in Neo4j Browser at http://localhost:7474

Example queries:
```cypher
// View all users
MATCH (u:User) RETURN u

// View conversation with a user
MATCH (u:User {id: "John Doe"})-[r]-(m:Message)
RETURN u, r, m

// Count messages per platform
MATCH (m:Message)
RETURN m.platform, count(m) as message_count
```

## Troubleshooting

### Neo4j Connection Issues
- Verify Neo4j is running: check http://localhost:7474
- Check credentials in `.env` file
- Ensure port 7687 is not blocked by firewall

### LLM API Errors
- Verify API key is correct in `.env`
- Check API key has sufficient credits/quota
- Try a different model if one fails

### CORS Errors
- The server allows all origins by default
- In production, update `allow_origins` in `main.py`

## Development

The server uses:
- **FastAPI** - Modern async web framework
- **Neo4j Python Driver** - Official Neo4j driver
- **OpenAI/Anthropic SDKs** - LLM provider clients
- **Pydantic** - Data validation
- **python-dotenv** - Environment variable management

## Production Deployment

For production:
1. Set `DEBUG=False` in `.env`
2. Use a production WSGI server (gunicorn)
3. Set up proper CORS origins
4. Use environment secrets management
5. Enable HTTPS
6. Set up Neo4j authentication and backups

## License

MIT License - See LICENSE file for details

