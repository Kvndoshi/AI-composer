"""
FastAPI backend for AI Message Composer
Handles message rewriting with RAG using Neo4j
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import time
import logging
from pathlib import Path
import sys
import asyncio

from dotenv import load_dotenv

# CRITICAL: Set Windows event loop policy BEFORE importing parsing (which imports Playwright)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from neo4j_service import Neo4jService
from llm_service import LLMService
from parsing import run_parsing
from supermemory_uploader import upload_markdown_to_supermemory
from supermemory_service import SuperMemoryService
from kg_pipeline import KGPipelineService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Message Composer API", version="1.0.0")

# CORS middleware for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
neo4j_service = Neo4jService(
    uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    user=os.getenv("NEO4J_USER", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password")
)

supermemory_service = SuperMemoryService(
    api_key=os.getenv("SUPERMEMORY_API_KEY"),
    container=os.getenv("SUPERMEMORY_CONTAINER", "ai-composer")
)

llm_service = LLMService(
    openai_key=os.getenv("OPENAI_API_KEY"),
    anthropic_key=os.getenv("ANTHROPIC_API_KEY")
)

# Initialize KG Pipeline (will be configured in startup)
kg_pipeline_service = None


# Pydantic models
class ConversationMessage(BaseModel):
    text: str
    is_outgoing: bool
    timestamp: str


class RewriteRequest(BaseModel):
    platform: str
    user_input: str
    conversation_context: List[ConversationMessage]
    recipient: str
    tone: Optional[str] = "professional"
    model: Optional[str] = None


class StoreConversationRequest(BaseModel):
    platform: str
    recipient: str
    message: str
    is_outgoing: bool
    timestamp: str


class RewriteResponse(BaseModel):
    rewritten_message: str
    original_message: str
    context_used: bool
    rag_context: Optional[str] = None


class StoreProfileRequest(BaseModel):
    platform: str
    profile_url: str
    profile_data: Optional[dict] = None
    cookies: Optional[List[dict]] = None  # Browser cookies for authenticated scraping


class ChatRequest(BaseModel):
    question: str
    platform: Optional[str] = None
    recipient: Optional[str] = None
    current_url: Optional[str] = None
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    answer: str
    context_used: bool


class SummarizeRequest(BaseModel):
    url: str
    title: Optional[str] = None
    cookies: Optional[List[dict]] = None  # Browser cookies for authenticated scraping


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "neo4j_connected": neo4j_service.test_connection(),
        "supermemory_connected": supermemory_service.test_connection(),
        "llm_available": llm_service.is_available()
    }


@app.post("/api/rewrite", response_model=RewriteResponse)
async def rewrite_message(request: RewriteRequest):
    """
    Rewrite a message using AI with RAG context from Neo4j
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"📝 REWRITE REQUEST RECEIVED")
    logger.info(f"   Platform: {request.platform}")
    logger.info(f"   Recipient: {request.recipient}")
    logger.info(f"   User Input: {request.user_input[:50]}..." if len(request.user_input) > 50 else f"   User Input: {request.user_input}")
    logger.info(f"   Tone: {request.tone}")
    logger.info(f"   Model: {request.model or os.getenv('DEFAULT_MODEL', 'fallback')}")
    
    try:
        # Step 1: Retrieve relevant past conversations from Neo4j
        neo4j_start = time.time()
        logger.info("🔍 Step 1: Querying Neo4j for conversation history...")
        rag_context = neo4j_service.get_conversation_history(
            recipient=request.recipient,
            platform=request.platform,
            limit=10
        )
        neo4j_time = time.time() - neo4j_start
        logger.info(f"   ✓ Neo4j query completed in {neo4j_time:.2f}s")
        logger.info(f"   ✓ Found {len(rag_context)} past messages")
        
        # Step 2: Build context string
        context_start = time.time()
        logger.info("📋 Step 2: Building context string...")
        context_str = ""
        if rag_context:
            context_str = "Previous conversation history:\n"
            for msg in rag_context:
                direction = "You" if msg["is_outgoing"] else request.recipient
                context_str += f"{direction}: {msg['message']}\n"
        
        # Add current conversation context
        if request.conversation_context:
            context_str += "\nCurrent conversation:\n"
            for msg in request.conversation_context:
                direction = "You" if msg.is_outgoing else request.recipient
                context_str += f"{direction}: {msg.text}\n"
        context_time = time.time() - context_start
        logger.info(f"   ✓ Context built in {context_time:.2f}s")
        logger.info(f"   ✓ Context length: {len(context_str)} characters")
        
        # Step 3: Rewrite message using LLM
        llm_start = time.time()
        model = request.model or os.getenv("DEFAULT_MODEL", "fallback")
        logger.info(f"🤖 Step 3: Calling LLM ({model})...")
        logger.info(f"   This may take 2-8 seconds depending on model...")
        rewritten = await llm_service.rewrite_message(
            user_input=request.user_input,
            context=context_str,
            tone=request.tone,
            platform=request.platform,
            model=model,
            recipient=request.recipient
        )
        llm_time = time.time() - llm_start
        logger.info(f"   ✓ LLM response received in {llm_time:.2f}s")
        logger.info(f"   ✓ Rewritten message length: {len(rewritten)} characters")
        
        total_time = time.time() - start_time
        logger.info(f"✅ REQUEST COMPLETED")
        logger.info(f"   Total time: {total_time:.2f}s")
        logger.info(f"   Breakdown: Neo4j={neo4j_time:.2f}s, Context={context_time:.2f}s, LLM={llm_time:.2f}s")
        logger.info("=" * 60)
        
        return RewriteResponse(
            rewritten_message=rewritten,
            original_message=request.user_input,
            context_used=bool(rag_context or request.conversation_context),
            rag_context=context_str if context_str else None
        )
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ ERROR after {total_time:.2f}s: {str(e)}")
        logger.error(f"   Error type: {type(e).__name__}")
        import traceback
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        logger.info("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/store-conversation")
async def store_conversation(request: StoreConversationRequest):
    """
    Store a conversation message in Neo4j (structured data) for future RAG retrieval
    """
    try:
        # Store in Neo4j as structured data
        neo4j_service.store_message(
            platform=request.platform,
            recipient=request.recipient,
            message=request.message,
            is_outgoing=request.is_outgoing,
            timestamp=request.timestamp
        )
        
        logger.info(f"✓ Message stored in Neo4j: {request.recipient}")
        
        return {
            "status": "success",
            "message": "Conversation stored in Neo4j"
        }
        
    except Exception as e:
        logger.error(f"Failed to store conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation-history/{recipient}")
async def get_conversation_history(recipient: str, platform: str = "linkedin", limit: int = 20):
    """
    Retrieve conversation history for a recipient
    """
    try:
        history = neo4j_service.get_conversation_history(
            recipient=recipient,
            platform=platform,
            limit=limit
        )
        
        return {"recipient": recipient, "messages": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversation-history/{recipient}")
async def delete_conversation_history(recipient: str, platform: str = "linkedin"):
    """
    Delete conversation history for a recipient
    """
    try:
        neo4j_service.delete_conversation_history(recipient, platform)
        return {"status": "success", "message": "Conversation history deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/store-profile")
async def store_profile(request: StoreProfileRequest):
    """
    Store profile data (from extension's DOM scraping or fallback to Crawl4AI)
    """
    try:
        # Check if profile_data was provided by the extension (LinkedIn DOM scraping)
        if request.profile_data and isinstance(request.profile_data, dict) and len(request.profile_data) > 0:
            logger.info(f"📊 Using profile data scraped from extension DOM")
            
            # Convert profile_data to markdown
            markdown_lines = ["# LinkedIn Profile\n"]
            markdown_lines.append(f"**URL:** {request.profile_url}\n")
            
            if request.profile_data.get('name'):
                markdown_lines.append(f"**Name:** {request.profile_data['name']}\n")
            if request.profile_data.get('headline'):
                markdown_lines.append(f"**Headline:** {request.profile_data['headline']}\n")
            if request.profile_data.get('location'):
                markdown_lines.append(f"**Location:** {request.profile_data['location']}\n")
            if request.profile_data.get('about'):
                markdown_lines.append(f"\n## About\n{request.profile_data['about']}\n")
            
            if request.profile_data.get('experience'):
                markdown_lines.append("\n## Experience\n")
                for exp in request.profile_data['experience']:
                    markdown_lines.append(f"### {exp.get('title', 'Position')}\n")
                    if exp.get('company'):
                        markdown_lines.append(f"**Company:** {exp['company']}\n")
                    if exp.get('duration'):
                        markdown_lines.append(f"**Duration:** {exp['duration']}\n")
                    markdown_lines.append("\n")
            
            if request.profile_data.get('education'):
                markdown_lines.append("\n## Education\n")
                for edu in request.profile_data['education']:
                    markdown_lines.append(f"### {edu.get('school', 'School')}\n")
                    if edu.get('degree'):
                        markdown_lines.append(f"**Degree:** {edu['degree']}\n")
                    if edu.get('years'):
                        markdown_lines.append(f"**Years:** {edu['years']}\n")
                    markdown_lines.append("\n")
            
            if request.profile_data.get('skills'):
                markdown_lines.append("\n## Skills\n")
                markdown_lines.append(", ".join(request.profile_data['skills']) + "\n")
            
            markdown_content = "\n".join(markdown_lines)
            logger.info(f"✓ Generated markdown from DOM data ({len(markdown_content)} chars)")
            
        else:
            # Fallback: Use Crawl4AI for non-LinkedIn or if DOM scraping failed
            logger.info(f"📄 Scraping profile using Crawl4AI from {request.profile_url}")
            markdown_path = Path(__file__).resolve().parent.parent / "scraped_data.md"
            
            if request.cookies:
                logger.info(f"   → Using {len(request.cookies)} browser cookies for authenticated access")
            await run_parsing(request.profile_url, markdown_path, cookies=request.cookies)
            logger.info(f"✓ Markdown generated at {markdown_path}")
            
            markdown_content = markdown_path.read_text(encoding='utf-8')
        
        # Store in Neo4j as unstructured data
        logger.info("💾 Storing profile in Neo4j...")
        neo4j_service.store_scraped_profile(
            url=request.profile_url,
            platform=request.platform,
            markdown_content=markdown_content
        )
        logger.info("✓ Profile stored in Neo4j")
        
        return {
            "status": "success",
            "content_length": len(markdown_content),
            "message": "Profile stored in Neo4j",
            "source": "dom_scraping" if request.profile_data else "crawl4ai"
        }
            
    except Exception as e:
        logger.error(f"Profile capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint with memory - retrieves context from Neo4j knowledge graph
    and maintains conversation history
    """
    try:
        # Step 1: Get chat history for context (use session_id from request)
        session_id = request.session_id or "default"
        chat_history = neo4j_service.get_chat_history(session_id=session_id, limit=10)
        
        # Step 2: Check if current URL has a stored page summary
        current_page = None
        if request.current_url:
            current_page = neo4j_service.get_page_summary(request.current_url)
            if current_page:
                logger.info(f"📄 Found stored page for current URL: {current_page['title']}")
        
        # Step 3: Get knowledge snippets from Neo4j
        snippets = neo4j_service.get_knowledge_snippets(
            platform=request.platform,
            recipient=request.recipient,
            limit=5
        )
        
        # Step 4: Build knowledge context
        knowledge_lines = []
        
        # Add current page content if available
        if current_page:
            knowledge_lines.append(f"Current Page: {current_page['title']}")
            knowledge_lines.append(f"URL: {current_page['url']}")
            knowledge_lines.append(f"Content:\n{current_page['content'][:2000]}")  # First 2000 chars
            knowledge_lines.append("")
        
        if snippets["messages"]:
            knowledge_lines.append("Recent conversations:")
            for msg in snippets["messages"]:
                direction = "You" if msg["is_outgoing"] else (request.recipient or "Contact")
                knowledge_lines.append(f"{direction}: {msg['message']}")
        
        if snippets["profiles"]:
            knowledge_lines.append("\nKnown profiles:")
            for profile in snippets["profiles"]:
                # Include profile content (markdown) for better context
                content = profile.get("content", "")
                if content:
                    knowledge_lines.append(f"\nProfile: {profile['url']}")
                    knowledge_lines.append(f"Content:\n{content}")
                else:
                    # Fallback to metadata if no content
                    summary = ", ".join([f"{k}: {v}" for k, v in profile["data"].items() if v])
                    knowledge_lines.append(f"- {profile['url']} ({profile['platform']}): {summary}")
        
        knowledge_context = "\n".join(knowledge_lines)
        
        # Step 4: Build chat context with history
        chat_context_lines = []
        if chat_history:
            chat_context_lines.append("Previous chat messages:")
            for msg in chat_history[-5:]:  # Last 5 messages for context
                chat_context_lines.append(f"{msg['role'].capitalize()}: {msg['message']}")
        
        # Combine knowledge and chat history
        full_context = ""
        if knowledge_context:
            full_context += f"Knowledge Base:\n{knowledge_context}\n\n"
        if chat_context_lines:
            full_context += "\n".join(chat_context_lines)
        
        # Step 5: Store user's question in chat history
        neo4j_service.store_chat_message(
            role="user",
            message=request.question,
            session_id=session_id
        )
        
        # Step 6: Ask LLM with full context
        # Build chat history string for LLM
        chat_history_str = "\n".join(chat_context_lines) if chat_context_lines else ""
        
        # Pass page content if in summarizer mode (session_id == "summarizer")
        answer = await llm_service.answer_question(
            question=request.question,
            knowledge_context=full_context,
            model=os.getenv("DEFAULT_MODEL", "fallback"),
            session_id=session_id,
            page_title=current_page['title'] if current_page else None,
            page_content=current_page['content'] if current_page else None,
            chat_history=chat_history_str
        )
        
        # Step 7: Store assistant's answer in chat history
        neo4j_service.store_chat_message(
            role="assistant",
            message=answer,
            session_id=session_id
        )
        
        logger.info(f"💬 Chat: Q={request.question[:50]}... A={answer[:50]}...")
        
        return ChatResponse(answer=answer, context_used=bool(full_context))
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat-history")
async def clear_chat_history(session_id: str = "default"):
    """
    Clear chat history to start a fresh conversation
    """
    try:
        neo4j_service.clear_chat_history(session_id=session_id)
        logger.info(f"🗑️ Cleared chat history for session: {session_id}")
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/summarize")
async def summarize_page(request: SummarizeRequest):
    """
    Scrape page, store as unstructured data, extract KG entities, and generate summary
    """
    try:
        markdown_path = Path(__file__).resolve().parent.parent / "scraped_data.md"
        
        # Step 1: Scrape the page using Crawl4AI
        logger.info(f"📄 Scraping page for summarization: {request.url}")
        if request.cookies:
            logger.info(f"   → Using {len(request.cookies)} browser cookies for authenticated access")
        await run_parsing(request.url, markdown_path, cookies=request.cookies)
        logger.info(f"✓ Markdown generated at {markdown_path}")
        
        # Step 2: Read the markdown content
        markdown_content = markdown_path.read_text(encoding='utf-8')
        
        # Step 3: Extract title from content if not provided
        title = request.title
        if not title:
            first_line = markdown_content.split('\n')[0].strip()
            if first_line.startswith('#'):
                title = first_line.lstrip('#').strip()
            else:
                title = request.url.split('/')[-1] or "Untitled Page"
        
        # Step 4: Store markdown in Neo4j
        logger.info(f"💾 Storing page summary in Neo4j: {title}")
        neo4j_service.store_page_summary(
            url=request.url,
            title=title,
            content=markdown_content
        )
        logger.info("✓ Page markdown stored")
        
        # Step 5: Run KG pipeline to extract structured entities
        kg_result = {"status": "skipped"}
        if kg_pipeline_service:
            logger.info("🧠 Running KG pipeline for page extraction...")
            kg_result = await kg_pipeline_service.process_page(
                markdown_path=markdown_path,
                page_url=request.url,
                page_title=title
            )
            if kg_result["status"] == "success":
                logger.info("✓ Page KG extraction complete")
            else:
                logger.warning(f"⚠️ KG extraction {kg_result['status']}: {kg_result.get('reason') or kg_result.get('error')}")
        else:
            logger.info("⚠️ KG pipeline not configured, skipping structured extraction")
        
        # Step 6: Generate automatic summary using LLM
        logger.info("📝 Generating automatic summary...")
        summary = await llm_service.answer_question(
            question="Summarize this page in a clear and concise way. Highlight the main points.",
            knowledge_context="",
            model=os.getenv("DEFAULT_MODEL", "fallback"),
            session_id="summarizer",
            page_title=title,
            page_content=markdown_content,
            chat_history=""
        )
        logger.info(f"✓ Summary generated ({len(summary)} chars)")
        
        return {
            "status": "success",
            "url": request.url,
            "title": title,
            "content_length": len(markdown_content),
            "kg_extraction": kg_result["status"],
            "summary": summary,
            "message": f"Page '{title}' stored and summarized"
        }
            
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize database schema on startup"""
    logger.info("=" * 60)
    logger.info("🚀 STARTING AI MESSAGE COMPOSER SERVER")
    logger.info("=" * 60)
    
    # Test Neo4j connection first
    try:
        neo4j_connected = neo4j_service.test_connection()
        if neo4j_connected:
            logger.info("✓ Neo4j connection test successful")
            try:
                neo4j_service.initialize_schema()
                logger.info("✓ Neo4j schema initialized")
            except Exception as e:
                logger.warning(f"⚠️  Neo4j schema initialization failed: {e}")
                logger.warning("   Server will continue, but some features may not work")
        else:
            logger.warning("⚠️  Neo4j connection failed - check your .env file")
            logger.warning("   Server will continue, but conversation storage won't work")
    except Exception as e:
        error_msg = str(e)
        if "AuthenticationRateLimit" in error_msg or "authentication" in error_msg.lower():
            logger.error("=" * 60)
            logger.error("❌ NEO4J AUTHENTICATION ERROR")
            logger.error("=" * 60)
            logger.error("The password in your .env file doesn't match your Neo4j database password.")
            logger.error("")
            logger.error("To fix this:")
            logger.error("1. Open Neo4j Desktop")
            logger.error("2. Check your database password")
            logger.error("3. Update the NEO4J_PASSWORD in your .env file")
            logger.error("4. Wait 1-2 minutes for the lockout to clear")
            logger.error("5. Restart the server")
            logger.error("")
            logger.error("If you forgot your password:")
            logger.error("- In Neo4j Desktop, click 'Reset Password' on your database")
            logger.error("=" * 60)
        else:
            logger.error(f"❌ Neo4j connection error: {e}")
        neo4j_connected = False
    
    # Test SuperMemory connection
    supermemory_connected = supermemory_service.test_connection()
    if supermemory_connected:
        logger.info("✓ SuperMemory connection test successful")
    else:
        logger.warning("⚠️  SuperMemory connection failed - check SUPERMEMORY_API_KEY in .env")
        logger.warning("   Server will continue, but conversation storage may not work")
    
    llm_available = llm_service.is_available()
    
    # Initialize KG Pipeline if LLM is available
    global kg_pipeline_service
    if llm_available and neo4j_connected:
        try:
            # Note: KG pipeline requires neo4j-graphrag LLM/Embedder interfaces
            # For now, we'll initialize it as None and it will be skipped
            # To enable: implement LLMInterface wrapper for llm_service
            kg_pipeline_service = None
            logger.info("⚠️  KG Pipeline: Requires neo4j-graphrag LLM wrapper (not yet implemented)")
            logger.info("   Profiles and pages will be stored as unstructured data only")
        except Exception as e:
            logger.warning(f"⚠️  KG Pipeline initialization failed: {e}")
            kg_pipeline_service = None
    else:
        kg_pipeline_service = None
        if not llm_available:
            logger.info("⚠️  KG Pipeline disabled: No LLM configured")
        if not neo4j_connected:
            logger.info("⚠️  KG Pipeline disabled: Neo4j not connected")
    
    logger.info(f"✓ Server started successfully")
    logger.info(f"✓ Neo4j connected: {neo4j_connected}")
    logger.info(f"✓ SuperMemory connected: {supermemory_connected}")
    logger.info(f"✓ LLM available: {llm_available}")
    logger.info(f"✓ KG Pipeline: {kg_pipeline_service is not None}")
    
    if llm_available:
        available_models = llm_service.get_available_models()
        logger.info(f"✓ Available models: {', '.join(available_models)}")
        default_model = os.getenv("DEFAULT_MODEL", "fallback")
        logger.info(f"✓ Default model: {default_model}")
    else:
        logger.warning("⚠️  No LLM API key configured - message rewriting won't work")
        logger.warning("   Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file")
    
    logger.info("=" * 60)
    logger.info("📡 Server ready at http://0.0.0.0:8000")
    logger.info("📚 API docs at http://localhost:8000/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    neo4j_service.close()
    print("✓ Server shutdown complete")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    # On Windows, force ProactorEventLoop for Playwright compatibility
    loop_config = "asyncio" if not sys.platform.startswith("win") else "asyncio"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        loop=loop_config
    )

