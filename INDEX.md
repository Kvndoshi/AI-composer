# AI Message Composer - File Index

Quick reference guide to all project files and their purposes.

## 📁 Root Directory

| File | Purpose | For |
|------|---------|-----|
| `README.md` | Main project documentation | Everyone |
| `QUICKSTART.md` | 10-minute quick start guide | First-time users |
| `SETUP_GUIDE.md` | Detailed setup instructions | Installation |
| `TESTING.md` | Testing procedures and scripts | QA/Testing |
| `PROJECT_SUMMARY.md` | Complete project overview | Hackathon judges |
| `INDEX.md` | This file - navigation guide | Developers |
| `LICENSE` | MIT License | Legal |
| `.gitignore` | Git ignore rules | Version control |

## 🔧 Extension Directory (`/extension`)

### Core Files
| File | Lines | Purpose |
|------|-------|---------|
| `manifest.json` | 45 | Chrome extension configuration (MV3) |
| `background.js` | 120 | Service worker - API communication |
| `content.js` | 450 | Content script - DOM scraping & UI injection |

### UI Files
| File | Lines | Purpose |
|------|-------|---------|
| `popup.html` | 80 | Extension popup interface |
| `popup.js` | 60 | Popup logic and stats |
| `options.html` | 130 | Settings page interface |
| `options.js` | 50 | Settings logic |

### Assets
| Directory | Purpose |
|-----------|---------|
| `icons/` | Extension icons (16x16, 48x48, 128x128) |

### Documentation
| File | Purpose |
|------|---------|
| `README.md` | Extension-specific documentation |

## 🖥️ Server Directory (`/server`)

### Core Files
| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 200 | FastAPI application & routes |
| `neo4j_service.py` | 250 | Neo4j database operations |
| `llm_service.py` | 150 | LLM provider integration |

### Configuration
| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `env.example` | Environment variables template |

### Testing & Documentation
| File | Purpose |
|------|---------|
| `test_api.py` | API testing script |
| `README.md` | Backend API documentation |

## 📊 File Statistics

```
Total Files: 23
Total Lines of Code: ~1,500
Documentation: ~3,000 lines
Languages: JavaScript, Python, Markdown
```

## 🔍 Quick Navigation

### "I want to..."

**...understand the project**
→ Start with `README.md`

**...set it up quickly**
→ Follow `QUICKSTART.md`

**...detailed installation**
→ Read `SETUP_GUIDE.md`

**...test the system**
→ Use `TESTING.md`

**...understand architecture**
→ See `PROJECT_SUMMARY.md`

**...modify the extension**
→ Edit files in `/extension`

**...change backend logic**
→ Edit files in `/server`

**...configure Neo4j queries**
→ Modify `neo4j_service.py`

**...change AI prompts**
→ Edit `llm_service.py`

**...add new platform support**
→ Update `content.js`

## 🎯 Key Code Locations

### Platform Detection
- **File:** `extension/content.js`
- **Function:** `detectPlatform()`
- **Lines:** ~20-30

### DOM Scraping
- **File:** `extension/content.js`
- **Functions:** `findLinkedInInputs()`, `findGmailInputs()`
- **Lines:** ~130-180

### Message Rewriting
- **File:** `server/llm_service.py`
- **Function:** `rewrite_message()`
- **Lines:** ~40-60

### Neo4j Storage
- **File:** `server/neo4j_service.py`
- **Function:** `store_message()`
- **Lines:** ~60-90

### Context Retrieval
- **File:** `server/neo4j_service.py`
- **Function:** `get_conversation_history()`
- **Lines:** ~100-130

### API Endpoints
- **File:** `server/main.py`
- **Routes:** `/health`, `/api/rewrite`, `/api/store-conversation`
- **Lines:** ~60-150

## 🔧 Configuration Files

### Extension Configuration
```
extension/manifest.json
  - Permissions
  - Content scripts
  - Background service worker
  - Host permissions
```

### Server Configuration
```
server/env.example
  - Neo4j connection
  - LLM API keys
  - Server settings
```

### Dependencies
```
server/requirements.txt
  - FastAPI
  - Neo4j driver
  - OpenAI/Anthropic SDKs
```

## 📝 Documentation Hierarchy

```
1. QUICKSTART.md          (10 min read)
   ↓
2. README.md              (20 min read)
   ↓
3. SETUP_GUIDE.md         (45 min read)
   ↓
4. PROJECT_SUMMARY.md     (30 min read)
   ↓
5. TESTING.md             (Reference)
```

## 🚀 Development Workflow

### 1. Initial Setup
1. Read `QUICKSTART.md`
2. Follow `SETUP_GUIDE.md`
3. Run `server/test_api.py`

### 2. Development
1. Modify code in `/extension` or `/server`
2. Test changes manually
3. Run automated tests

### 3. Testing
1. Follow `TESTING.md`
2. Run `server/test_api.py`
3. Manual testing on LinkedIn/Gmail

### 4. Deployment
1. Review `PROJECT_SUMMARY.md` deployment section
2. Configure production environment
3. Deploy server and publish extension

## 📚 Learning Path

### For Beginners
1. `README.md` - Understand what it does
2. `QUICKSTART.md` - Get it running
3. `extension/content.js` - See how it works
4. Experiment with different messages

### For Developers
1. `PROJECT_SUMMARY.md` - Architecture overview
2. `server/main.py` - API structure
3. `server/neo4j_service.py` - Database operations
4. `server/llm_service.py` - AI integration
5. `extension/content.js` - Frontend logic

### For Hackathon Judges
1. `PROJECT_SUMMARY.md` - Complete overview
2. `README.md` - Features and innovation
3. Live demo on LinkedIn/Gmail
4. `TESTING.md` - Quality assurance

## 🔗 External Resources

### Documentation
- Chrome Extensions: https://developer.chrome.com/docs/extensions/
- FastAPI: https://fastapi.tiangolo.com/
- Neo4j: https://neo4j.com/docs/
- OpenAI API: https://platform.openai.com/docs/
- Anthropic API: https://docs.anthropic.com/

### Tools
- Neo4j Desktop: https://neo4j.com/download/
- Neo4j Browser: http://localhost:7474 (when running)
- API Docs: http://localhost:8000/docs (when running)

## 📞 Support

### Issues
- Check `SETUP_GUIDE.md` troubleshooting section
- Review `TESTING.md` for debugging
- Check server logs for errors
- Check Chrome console for extension errors

### Contact
- GitHub Issues: [Repository URL]
- Email: [Contact Email]

## 🎓 Code Comments

All code files include:
- Function docstrings
- Inline comments for complex logic
- Type hints (Python)
- JSDoc comments (JavaScript)

## 🔄 Version Control

### Git Workflow
```bash
# Clone repository
git clone [repository-url]

# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Description"

# Push changes
git push origin feature/your-feature
```

### .gitignore Coverage
- Python cache files
- Environment variables (.env)
- IDE files
- Neo4j data
- Logs and temporary files

## 📊 Metrics

### Code Quality
- Modular architecture
- Separation of concerns
- Error handling throughout
- Async/await patterns
- Type safety (Pydantic)

### Documentation Quality
- README for each component
- Inline code comments
- API documentation
- Setup guides
- Testing procedures

## 🎯 Next Steps

After reviewing this index:
1. Choose your path (beginner/developer/judge)
2. Follow the recommended reading order
3. Set up the project
4. Explore the code
5. Test the features
6. Customize for your needs

---

**Last Updated:** 2024
**Maintained by:** AI Message Composer Team
**License:** MIT

