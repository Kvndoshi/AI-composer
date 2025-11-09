import asyncio
import sys
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Thread pool for running Crawl4AI in a separate thread with its own event loop
_executor = ThreadPoolExecutor(max_workers=1)

def scrape_linkedin_metadata(url: str, cookies: Optional[List[Dict]] = None) -> str:
    """
    Scrape LinkedIn profile using Open Graph metadata and simple HTTP request.
    This is more reliable than Crawl4AI for LinkedIn profiles.
    
    Args:
        url: LinkedIn profile URL
        cookies: Optional cookies (converted to requests format)
        
    Returns:
        Markdown formatted profile information
    """
    try:
        # Convert Chrome cookies to requests format
        cookie_dict = {}
        if cookies:
            for cookie in cookies:
                cookie_dict[cookie.get('name', '')] = cookie.get('value', '')
        
        # Make HTTP request with cookies
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, cookies=cookie_dict, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract Open Graph metadata
        metadata = {}
        for meta in soup.find_all('meta'):
            property_name = meta.get('property', '') or meta.get('name', '')
            content = meta.get('content', '')
            if property_name and content:
                metadata[property_name] = content
        
        # Build markdown from metadata
        markdown_lines = [f"# LinkedIn Profile\n"]
        markdown_lines.append(f"**URL:** {url}\n")
        
        # Name
        if 'og:title' in metadata:
            markdown_lines.append(f"**Name:** {metadata['og:title']}\n")
        elif 'twitter:title' in metadata:
            markdown_lines.append(f"**Name:** {metadata['twitter:title']}\n")
        
        # Description/Headline
        if 'og:description' in metadata:
            markdown_lines.append(f"**Headline:** {metadata['og:description']}\n")
        elif 'twitter:description' in metadata:
            markdown_lines.append(f"**Headline:** {metadata['twitter:description']}\n")
        elif 'description' in metadata:
            markdown_lines.append(f"**Headline:** {metadata['description']}\n")
        
        # Image
        if 'og:image' in metadata:
            markdown_lines.append(f"**Profile Image:** {metadata['og:image']}\n")
        
        # Try to extract additional info from page title and meta tags
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            title_text = title_tag.text.strip()
            # LinkedIn titles often have format: "Name | LinkedIn"
            if '|' in title_text:
                parts = title_text.split('|')
                if len(parts) > 1:
                    markdown_lines.append(f"**Full Title:** {parts[0].strip()}\n")
        
        # Look for structured data (JSON-LD)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Person':
                        if 'name' in data:
                            markdown_lines.append(f"**Name (from structured data):** {data['name']}\n")
                        if 'jobTitle' in data:
                            markdown_lines.append(f"**Job Title:** {data['jobTitle']}\n")
                        if 'worksFor' in data and isinstance(data['worksFor'], dict):
                            markdown_lines.append(f"**Company:** {data['worksFor'].get('name', '')}\n")
                        if 'alumniOf' in data:
                            if isinstance(data['alumniOf'], list):
                                for school in data['alumniOf']:
                                    if isinstance(school, dict):
                                        markdown_lines.append(f"**Education:** {school.get('name', '')}\n")
                            elif isinstance(data['alumniOf'], dict):
                                markdown_lines.append(f"**Education:** {data['alumniOf'].get('name', '')}\n")
            except:
                pass
        
        # Add all other metadata as additional info
        markdown_lines.append("\n## Additional Metadata\n")
        for key, value in metadata.items():
            if key not in ['og:title', 'og:description', 'og:image', 'twitter:title', 'twitter:description']:
                markdown_lines.append(f"- **{key}:** {value}\n")
        
        markdown_content = '\n'.join(markdown_lines)
        
        print(f"✓ Scraped LinkedIn metadata: {len(markdown_content)} characters")
        return markdown_content
        
    except Exception as e:
        print(f"❌ LinkedIn metadata scraping failed: {e}")
        return f"# LinkedIn Profile\n\n**URL:** {url}\n\n**Error:** Failed to scrape profile metadata.\n\nError details: {str(e)}"

def _run_in_new_loop(url, out, cookies=None):
    """Run Crawl4AI in a new event loop (for Windows compatibility)"""
    # Set Windows event loop policy in this thread
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(_crawl(url, out, cookies))
    finally:
        loop.close()

async def _crawl(url, out, cookies=None):
    """The actual Crawl4AI logic with cookie support"""
    # Step 1: Create a pruning filter
    prune_filter = PruningContentFilter(
        threshold=0.45,
        threshold_type="dynamic",
        min_word_threshold=5      
    )

    # Step 2: Insert it into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    # Step 3: Configure browser with headless mode
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )

    # Step 4: Pass it to CrawlerRunConfig
    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # If cookies are provided, set them before crawling
        extra_args = {}
        if cookies:
            # Convert cookie list to Playwright format
            extra_args['cookies'] = cookies
        
        result = await crawler.arun(
            url=url, 
            config=config,
            **extra_args
        )

        if result.success:
            markdown_content = result.markdown.fit_markdown
            
            # Check if we got a sign-in page (common indicators)
            signin_indicators = [
                "sign in",
                "log in",
                "join now",
                "create account",
                "authentication required"
            ]
            
            content_lower = markdown_content.lower()
            is_signin_page = any(indicator in content_lower for indicator in signin_indicators)
            
            # If it's mostly a sign-in page and very short, it's likely blocked
            if is_signin_page and len(markdown_content) < 500:
                print("⚠️ Warning: Detected sign-in page. LinkedIn may be blocking the request.")
                print("   Tip: The extension should pass browser cookies for authenticated access.")
            
            print("Raw Markdown length:", len(result.markdown.raw_markdown))
            print("Fit Markdown length:", len(markdown_content))
            
            with open(out, "w", encoding="utf-8") as f:
                f.write(markdown_content)
        else:
            print("Error:", result.error_message)
            # Write error to file so we know what happened
            with open(out, "w", encoding="utf-8") as f:
                f.write(f"# Scraping Error\n\nFailed to scrape {url}\n\nError: {result.error_message}")

async def run_parsing(url, out, cookies: Optional[List[Dict]] = None):
    """Called from main.py - runs Crawl4AI in a separate thread
    
    Args:
        url: URL to scrape
        out: Output file path
        cookies: Optional list of cookies in Playwright format
                 [{"name": "li_at", "value": "...", "domain": ".linkedin.com", ...}]
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _run_in_new_loop, url, str(out), cookies)