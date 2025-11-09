# Quick Start - AI Message Composer

Get up and running in 10 minutes!

## Prerequisites

- Chrome browser
- Python 3.9+
- OpenAI or Anthropic API key

## 1. Install Neo4j (5 minutes)

**Easiest method - Neo4j Desktop:**

1. Download: https://neo4j.com/download/
2. Install and launch
3. Create new database with password
4. Click "Start"

**Alternative - Docker:**
```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:latest
```

## 2. Setup Backend (3 minutes)

```bash
# Navigate to server
cd claudehacksextension/server

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp env.example .env

# Edit .env - add your credentials:
# NEO4J_PASSWORD=your_password
# OPENAI_API_KEY=your_key

# Start server
python main.py
```

Verify: http://localhost:8000/health should show "healthy"

## 3. Install Extension (2 minutes)

1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `claudehacksextension/extension` folder
5. Click extension icon → Settings
6. Verify settings and save

## 4. Test It! (1 minute)

1. Go to LinkedIn or Gmail
2. Start composing a message
3. Type: "hey can we meet tomorrow?"
4. Click "✨ AI Rewrite" button
5. Watch your message transform!

## Troubleshooting

**Server won't start?**
- Check Neo4j is running
- Verify API key in .env

**Button doesn't appear?**
- Refresh the page
- Check extension is enabled

**Need help?** See SETUP_GUIDE.md for detailed instructions.

---

**That's it!** You're ready to write professional messages with AI assistance. 🚀

