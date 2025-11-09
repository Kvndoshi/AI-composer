# AI Composer - Your Personal Writing Assistant with Memory

**Your personal composer that remembers everything and summarizes anything.**

AI Composer is a Chrome extension that transforms casual drafts into professional messages with one click. It stores every conversation in a knowledge graph, so it never forgets context, and can summarize any webpage for instant insights.

---

## 🎯 **Features**

### **1. Intelligent Message Rewriting**
- Write naturally, get professional output instantly
- **Platform-aware**: LinkedIn messages are casual and conversational, Gmail emails are polite and professional
- No more copy-pasting to ChatGPT or Grammarly

### **2. Knowledge Graph Memory**
- **Never forgets**: Stores every conversation in Neo4j
- **Context-aware**: Remembers previous exchanges when you message someone again
- **Personalized**: The more you use it, the smarter it gets

### **3. Profile Intelligence**
- **Capture profiles**: Extract LinkedIn profile data directly from the DOM
- **Smart matching**: Ask "Am I a good fit for this professor's research?"
- **Structured storage**: Name, headline, experience, education, and skills stored in Neo4j

### **4. Page Summarizer**
- **One-click summaries**: Instantly summarize any webpage
- **Interactive Q&A**: Ask follow-up questions about the content
- **Separate memory**: Keeps summarizer conversations isolated

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+
- Neo4j Desktop (or Neo4j instance)
- Chrome browser
- Anthropic API key (for Claude Sonnet 4)

### **Installation**

#### **1. Clone the Repository**
```bash
git clone https://github.com/Kvndoshi/AI-composer.git
cd AI-composer
```

#### **2. Set Up Backend**
```bash
cd server
pip install -r requirements-simple.txt
```

#### **3. Configure Environment**
```bash
cp env.example .env
# Edit .env with your API keys and Neo4j credentials
```

**Required `.env` variables:**
```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# LLM API Key
ANTHROPIC_API_KEY=your_anthropic_key_here

# Default Model
DEFAULT_MODEL=claude-sonnet-4-5-20250929
```

#### **4. Start Neo4j**
- Open Neo4j Desktop
- Create a new database (or use existing)
- Set password to match your `.env` file
- Start the database

#### **5. Run Backend Server**
```bash
python main.py
```

Server will start on `http://localhost:8000`

#### **6. Load Chrome Extension**
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extension` folder from this repository
5. The extension icon should appear in your toolbar

---

## 📖 **Usage**

### **Message Rewriting**

1. **Go to LinkedIn or Gmail**
2. **Write your message** in your own words
3. **Click "Generate"** in the floating circle
4. **Your message is rewritten** professionally and inserted automatically

**Example:**
- **Your draft**: "hi we met at event yesterday, how are you doing"
- **AI output**: "Hey! It was great meeting you at the event yesterday. Hope you're doing well!"

### **Profile Capture**

1. **Go to any LinkedIn profile**
2. **Click the floating circle** → **"Capture Profile"**
3. **Profile data is extracted** from the DOM and stored in Neo4j
4. **Ask questions** like "Where does [name] study?" or "What skills does [name] have?"

### **Page Summarizer**

1. **Go to any webpage** (Wikipedia, research paper, documentation)
2. **Click the floating circle** → **"Summarize Page"**
3. **Get an instant summary** from Claude Sonnet 4
4. **Ask follow-up questions** about the page content

### **Chat with Knowledge Graph**

1. **Click the floating circle** → **"Chat"**
2. **Ask questions** about your stored conversations, profiles, or pages
3. **Get personalized answers** based on your knowledge graph

---

## 🏗️ **Architecture**

### **Frontend (Chrome Extension)**
- **Manifest V3**: Modern Chrome extension architecture
- **Content Scripts**: Inject UI and scrape page content
- **Background Service Worker**: Handle API communication
- **Draggable Floating UI**: Accessible on any website

### **Backend (FastAPI + Python)**
- **FastAPI**: High-performance async API server
- **Crawl4AI**: Advanced web scraping with clean markdown
- **Neo4j**: Graph database for conversations, profiles, and relationships
- **Claude Sonnet 4**: State-of-the-art LLM for rewriting and chat

### **Data Flow**
```
User writes message
        ↓
Extension scrapes page context
        ↓
Backend retrieves relevant history from Neo4j
        ↓
Claude Sonnet 4 rewrites with context
        ↓
Message inserted back into input field
        ↓
User clicks "Send" → Stored in knowledge graph
```

---

## 🛠️ **Tech Stack**

| Component | Technology |
|-----------|------------|
| **Extension** | JavaScript (Manifest V3) |
| **Backend** | Python, FastAPI |
| **Database** | Neo4j (Graph Database) |
| **LLM** | Anthropic Claude Sonnet 4 |
| **Web Scraping** | Crawl4AI, Playwright, BeautifulSoup |
| **Async Processing** | asyncio, ThreadPoolExecutor |

---

## 📂 **Project Structure**

```
AI-composer/
├── extension/              # Chrome extension
│   ├── manifest.json      # Extension configuration
│   ├── content.js         # Content script (DOM interaction)
│   ├── background.js      # Service worker (API calls)
│   ├── popup.html         # Extension popup
│   ├── options.html       # Settings page
│   └── icons/             # Extension icons
├── server/                # Backend API
│   ├── main.py           # FastAPI application
│   ├── llm_service.py    # LLM integration
│   ├── neo4j_service.py  # Neo4j database operations
│   ├── parsing.py        # Web scraping (Crawl4AI)
│   ├── kg_pipeline.py    # Knowledge graph pipeline
│   └── requirements-simple.txt  # Python dependencies
├── .gitignore
├── README.md
└── LICENSE
```

---

## 🎨 **Key Features in Detail**

### **Platform-Specific Prompts**

**LinkedIn Style:**
- Short and natural (2-3 sentences max)
- Friendly, networking tone
- No formal closings like "Best regards"

**Gmail Style:**
- Polite and professional
- Warm but professional tone
- No stiff closings like "Sincerely"

### **Knowledge Graph Structure**

**Node Types:**
- `:Message` - Conversation messages
- `:Contact` - Recipients/contacts
- `:ScrapedProfile` - Captured profiles
- `:ChatMessage` - Chat history
- `:PageSummary` - Summarized pages

**Relationships:**
- `(:Message)-[:SENT_TO]->(:Contact)`
- `(:ChatMessage)-[:IN_SESSION]->(:Session)`
- `(:Profile)-[:HAS_EXPERIENCE]->(:Experience)`

### **Separate Chat Memories**

- **Default chat**: General knowledge graph queries
- **Summarizer chat**: Page-specific Q&A (session_id: "summarizer")

---

## 🔒 **Privacy & Security**

- ✅ All data stored locally in your Neo4j database
- ✅ API keys stored in `.env` (never committed to git)
- ✅ Cookies only sent to your localhost backend
- ✅ No data sent to third parties (except LLM API for processing)

---

## 🐛 **Troubleshooting**

### **Extension not loading**
- Check that you've enabled "Developer mode" in `chrome://extensions/`
- Make sure you selected the `extension` folder (not the root folder)
- Check browser console for errors

### **Backend connection failed**
- Ensure backend is running on `http://localhost:8000`
- Check extension settings (click extension icon → Options)
- Verify API URL is set to `http://localhost:8000`

### **Neo4j connection failed**
- Verify Neo4j Desktop is running
- Check credentials in `.env` match your Neo4j database
- Test connection: `bolt://localhost:7687`

### **LLM not working**
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check API key is valid at https://console.anthropic.com/
- Ensure `DEFAULT_MODEL=claude-sonnet-4-5-20250929`

---

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📝 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 **Acknowledgments**

- Built with [Crawl4AI](https://github.com/unclecode/crawl4ai) for web scraping
- Powered by [Anthropic Claude](https://www.anthropic.com/) for LLM capabilities
- Uses [Neo4j](https://neo4j.com/) for graph database storage
- Built with [FastAPI](https://fastapi.tiangolo.com/) for the backend

---

## 📧 **Contact**

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ by a first-time JavaScript developer who wanted to make professional communication effortless for everyone.**
