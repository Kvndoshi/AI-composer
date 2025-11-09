# Complete Setup Guide - AI Message Composer

Step-by-step guide to get the AI Message Composer up and running.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Chrome browser installed
- [ ] Python 3.9 or higher installed
- [ ] pip (Python package manager) installed
- [ ] Git (optional, for cloning)
- [ ] OpenAI API key OR Anthropic API key
- [ ] 2GB free disk space

## Step 1: Install Neo4j Database

### Option A: Neo4j Desktop (Recommended for Beginners)

1. **Download Neo4j Desktop**
   - Visit: https://neo4j.com/download/
   - Click "Download Neo4j Desktop"
   - No account required for local use

2. **Install Neo4j Desktop**
   - Run the installer
   - Follow installation wizard
   - Launch Neo4j Desktop

3. **Create a Database**
   - Click "New" → "Create Project"
   - Click "Add" → "Local DBMS"
   - Name: `ai-composer`
   - Password: Choose a strong password (save this!)
   - Version: Use latest (5.x)
   - Click "Create"

4. **Start the Database**
   - Click "Start" on your database
   - Wait for status to show "Active"
   - Note the connection details:
     - Bolt URL: `bolt://localhost:7687`
     - HTTP URL: `http://localhost:7474`

5. **Test Connection**
   - Click "Open" → "Neo4j Browser"
   - You should see the Neo4j Browser interface
   - Run: `:server status`
   - Should show "Connected"

### Option B: Docker (For Advanced Users)

```bash
# Pull and run Neo4j container
docker run -d \
  --name ai-composer-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_secure_password \
  -v neo4j-data:/data \
  neo4j:latest

# Verify it's running
docker ps | grep neo4j

# Access browser at http://localhost:7474
```

### Option C: Neo4j Aura Free (Cloud)

1. Visit: https://neo4j.com/cloud/aura/
2. Sign up for free account
3. Create a free instance
4. Save the connection URI and credentials
5. Use this URI in your `.env` file

## Step 2: Get LLM API Key

### Option A: OpenAI (Recommended)

1. **Create OpenAI Account**
   - Visit: https://platform.openai.com/signup
   - Sign up with email or Google

2. **Add Payment Method**
   - Go to: https://platform.openai.com/account/billing
   - Add credit card (required even for free tier)
   - Add $5-10 credit for testing

3. **Create API Key**
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Name it: "AI Message Composer"
   - Copy the key (starts with `sk-`)
   - ⚠️ Save it securely - you won't see it again!

### Option B: Anthropic Claude

1. **Create Anthropic Account**
   - Visit: https://console.anthropic.com/
   - Sign up with email

2. **Get API Key**
   - Go to: https://console.anthropic.com/settings/keys
   - Click "Create Key"
   - Copy the key (starts with `sk-ant-`)
   - Save it securely

## Step 3: Set Up Backend Server

1. **Navigate to Server Directory**
```bash
cd claudehacksextension/server
```

2. **Create Virtual Environment (Recommended)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

If you get errors, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Create Environment File**
```bash
# Copy the example
cp env.example .env

# Or on Windows
copy env.example .env
```

5. **Edit .env File**

Open `.env` in a text editor and fill in:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# LLM API Key (add at least one)
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Server Configuration (leave as is)
HOST=0.0.0.0
PORT=8000
DEBUG=True
DEFAULT_MODEL=gpt-4
```

6. **Start the Server**
```bash
python main.py
```

You should see:
```
✓ Server started successfully
✓ Neo4j connected: True
✓ LLM available: True
INFO:     Uvicorn running on http://0.0.0.0:8000
```

7. **Test the Server**

Open a new terminal and run:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "llm_available": true
}
```

Or visit in browser: http://localhost:8000/docs

## Step 4: Install Chrome Extension

1. **Open Chrome Extensions Page**
   - Open Chrome browser
   - Go to: `chrome://extensions/`
   - Or: Menu → Extensions → Manage Extensions

2. **Enable Developer Mode**
   - Toggle "Developer mode" in top-right corner
   - Should turn blue/enabled

3. **Load Extension**
   - Click "Load unpacked"
   - Navigate to: `claudehacksextension/extension`
   - Select the folder
   - Click "Select Folder"

4. **Verify Installation**
   - Extension should appear in the list
   - You should see "AI Message Composer"
   - Status should be "Enabled"

5. **Pin Extension (Optional)**
   - Click puzzle icon in Chrome toolbar
   - Find "AI Message Composer"
   - Click pin icon to keep it visible

## Step 5: Configure Extension

1. **Open Extension Popup**
   - Click the extension icon in Chrome toolbar
   - You should see the popup interface

2. **Check Connection Status**
   - Should show "✓ Connected to backend"
   - If not, click "Test Connection"
   - If still failing, verify server is running

3. **Open Settings**
   - Click "Settings" button
   - Settings page will open in new tab

4. **Configure Settings**
   - **Backend API URL**: `http://localhost:8000` (should be default)
   - **LLM Model**: Choose based on your API key
     - OpenAI: `gpt-4` or `gpt-3.5-turbo`
     - Anthropic: `claude-3-sonnet` or `claude-3-opus`
   - **Default Tone**: Choose `professional`
   - **Auto-store conversations**: Check this box
   - Click "Save Settings"

5. **Verify Configuration**
   - Should see "Settings saved successfully!"
   - Close settings tab
   - Click extension icon again
   - Click "Test Connection"
   - Should show "✓ Connected to backend"

## Step 6: Test the Extension

### Test on LinkedIn

1. **Navigate to LinkedIn**
   - Go to: https://www.linkedin.com/
   - Log in to your account

2. **Open Messages**
   - Click "Messaging" icon
   - Select any conversation or start a new one

3. **Test Message Rewrite**
   - Type a casual message: "hey can we connect tomorrow?"
   - Look for "✨ AI Rewrite" button near the message field
   - Click the button
   - Wait 2-3 seconds
   - Your message should be rewritten professionally!

### Test on Gmail

1. **Navigate to Gmail**
   - Go to: https://mail.google.com/
   - Log in to your account

2. **Compose Email**
   - Click "Compose"
   - In the message body, type: "hey thanks for the info, lets meet soon"
   - Look for "✨ AI Rewrite" button
   - Click it
   - Message should be rewritten

### Verify Neo4j Storage

1. **Open Neo4j Browser**
   - Go to: http://localhost:7474
   - Log in with your Neo4j credentials

2. **Check Data**
   - Run this query:
   ```cypher
   MATCH (u:User)-[r]-(m:Message)
   RETURN u, r, m
   LIMIT 10
   ```
   - You should see nodes and relationships
   - This confirms messages are being stored

## Troubleshooting

### Server Won't Start

**Error: "Address already in use"**
```bash
# Port 8000 is taken, use different port
PORT=8001 python main.py
# Then update extension settings to http://localhost:8001
```

**Error: "No module named 'fastapi'"**
```bash
# Virtual environment not activated or dependencies not installed
pip install -r requirements.txt
```

### Neo4j Connection Failed

**Error: "Unable to connect to Neo4j"**
- Verify Neo4j is running (check Neo4j Desktop)
- Check password in `.env` matches Neo4j password
- Try connecting manually at http://localhost:7474

### Extension Not Working

**Button doesn't appear**
- Refresh the LinkedIn/Gmail page
- Check Chrome console for errors (F12)
- Verify extension is enabled in chrome://extensions/

**"Backend not connected" error**
- Ensure server is running: http://localhost:8000/health
- Check extension settings have correct URL
- Check browser console for CORS errors

### LLM API Errors

**Error: "Invalid API key"**
- Verify API key in `.env` is correct
- Check for extra spaces or quotes
- Regenerate API key if needed

**Error: "Insufficient quota"**
- Add credits to your OpenAI/Anthropic account
- Try a cheaper model (gpt-3.5-turbo)

## Next Steps

Once everything is working:

1. **Test Different Tones**
   - Try professional, friendly, formal, casual
   - See how the AI adapts

2. **Build Conversation History**
   - Use the extension for a few days
   - Watch how context improves responses

3. **Explore Neo4j Graph**
   - Visualize your conversation network
   - Run analytics queries

4. **Customize Prompts**
   - Edit `llm_service.py` to adjust AI behavior
   - Restart server after changes

## Getting Help

If you're stuck:

1. Check server logs for errors
2. Check Chrome console (F12) for extension errors
3. Verify all services are running:
   - Neo4j: http://localhost:7474
   - Server: http://localhost:8000/health
4. Review error messages carefully
5. Try the troubleshooting steps above

## Success Checklist

- [ ] Neo4j running and accessible
- [ ] Backend server running on port 8000
- [ ] Health check returns "healthy"
- [ ] Extension installed and enabled in Chrome
- [ ] Extension shows "Connected to backend"
- [ ] Button appears on LinkedIn/Gmail
- [ ] Message rewrite works
- [ ] Messages stored in Neo4j

If all checked, you're ready to go! 🎉

---

**Estimated Setup Time**: 30-45 minutes

**Difficulty**: Intermediate (requires basic command line knowledge)

**Support**: Open an issue if you encounter problems not covered here.

