# AI Composer - Your Personal Writing Assistant with Memory

> **⚠️ IMPORTANT NOTE:** Docs doesn't show full functionality.

**Imagine AI able to scrape any website and store in an advanced memory which uses knowledge graphs, and you can chat endlessly. Helps you compose any email you write in your own words... also chat with any webpage, professor profile, you can even upload GitHub and understand the context by URL. You can chat with your own projects, assignments, and much more.**

---

## 🎯 **What it does**

AI Composer transforms your casual drafts into professional messages with one click. Write naturally, and it generates polished LinkedIn messages or emails tailored to the platform.

**Key Features:**

- **Knowledge Graph Memory**: Stores every conversation in Neo4j, so it never forgets. Next time you message someone, it remembers your entire chat history.

- **Profile Intelligence**: Scrapes profiles (professors, professionals, companies) and lets you chat with the LLM to ask "Am I a good fit for their research project?"

- **Page Summarizer**: Instantly summarizes any webpage and answers questions about the content—perfect for research papers, documentation, or Wikipedia articles.

- **Universal Content Scraper**: Captures notes, class materials, workflows, and any webpage content. Store everything in your personal knowledge base.

- **Interactive Learning**: Generate custom quizzes, study materials, and flashcards from any content. Play educational games through natural conversation—no interface needed.

- **Infinite Context**: Chat with your entire knowledge base. AI Composer searches through all your stored conversations, profiles, notes, and scraped content to give personalized answers. It never forgets.

**All through natural conversation. No extra interfaces. Just chat, learn, and let AI remember everything for you.** 🚀

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

1. **Message Rewriting**: Write naturally → Click "Generate" → Get professional output
2. **Profile Capture**: Visit any LinkedIn profile → Click "Capture Profile" → Chat with their profile
3. **Page Summarizer**: On any webpage → Click "Summarize Page" → Get instant summary + Q&A
4. **Chat**: Ask questions about your stored conversations, profiles, or pages

---

## 🛠️ **Tech Stack**

- **Extension**: JavaScript (Manifest V3)
- **Backend**: Python, FastAPI
- **Database**: Neo4j (Knowledge Graph)
- **LLM**: Anthropic Claude Sonnet 4
- **Web Scraping**: Crawl4AI, Playwright

---

## 🐛 **Troubleshooting**

- **Extension not loading**: Enable "Developer mode" in `chrome://extensions/` and load the `extension` folder
- **Backend connection failed**: Ensure backend is running on `http://localhost:8000`
- **Neo4j connection failed**: Verify Neo4j Desktop is running and credentials in `.env` are correct
- **LLM not working**: Verify `ANTHROPIC_API_KEY` in `.env` is valid

---

## 📝 **License**

MIT License - see LICENSE file for details.

---

**Built with ❤️ for making professional communication and knowledge management effortless.**
