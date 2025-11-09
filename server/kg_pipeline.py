"""
Knowledge Graph Pipeline using Neo4j GraphRAG
Processes unstructured data (profiles, pages) into structured graph entities
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from neo4j import Driver
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import LLMInterface
from neo4j_graphrag.embeddings import Embedder

logger = logging.getLogger(__name__)


# Profile extraction schema
PROFILE_ENTITIES = [
    "Person",
    {"label": "Company", "description": "Company or organization where person worked"},
    {"label": "Skill", "description": "Professional skill or technology"},
    {"label": "Portfolio", "description": "Project, portfolio item, or work sample"},
    {"label": "Location", "properties": [{"name": "city", "type": "STRING"}]},
]

PROFILE_RELATIONS = [
    {"label": "WORKS_AT", "properties": [{"name": "role", "type": "STRING"}, {"name": "start_date", "type": "STRING"}, {"name": "end_date", "type": "STRING"}]},
    "HAS_SKILL",
    "HAS_PORTFOLIO",
    "LOCATED_AT",
    {"label": "HAS_LINK", "description": "External link (GitHub, LinkedIn, etc.)"},
]

# Page summarization schema (open-ended)
PAGE_ENTITIES = [
    "Person",
    "Organization",
    "Concept",
    "Technology",
    "Event",
    "Location",
    "Product",
    "Topic",
]

PAGE_RELATIONS = [
    "CREATED_BY",
    "PART_OF",
    "RELATED_TO",
    "DEVELOPED_BY",
    "USED_IN",
    "LOCATED_AT",
    "FOUNDED_BY",
    "WORKS_ON",
    "MENTIONS",
]


class KGPipelineService:
    """Service for running knowledge graph extraction pipelines"""
    
    def __init__(
        self,
        neo4j_driver: Driver,
        llm: Optional[LLMInterface] = None,
        embedder: Optional[Embedder] = None
    ):
        self.driver = neo4j_driver
        self.llm = llm
        self.embedder = embedder
    
    async def process_profile(
        self,
        markdown_path: Path,
        profile_url: str
    ) -> Dict[str, Any]:
        """
        Process a profile markdown file through the KG pipeline
        
        Args:
            markdown_path: Path to the markdown file
            profile_url: URL of the profile (used as source identifier)
            
        Returns:
            Dictionary with extraction results
        """
        if not self.llm:
            logger.warning("No LLM configured for KG pipeline, skipping profile extraction")
            return {"status": "skipped", "reason": "no_llm"}
        
        try:
            logger.info(f"🧠 Running KG pipeline for profile: {profile_url}")
            
            kg_builder = SimpleKGPipeline(
                llm=self.llm,
                driver=self.driver,
                embedder=self.embedder,
                from_pdf=False,  # We're processing markdown text
                entities=PROFILE_ENTITIES,
                relations=PROFILE_RELATIONS,
            )
            
            # Run the pipeline
            result = await kg_builder.run_async(file_path=str(markdown_path))
            
            logger.info(f"✓ Profile KG extraction complete")
            
            # Tag extracted nodes with source URL
            self._tag_nodes_with_source(profile_url, "profile")
            
            return {
                "status": "success",
                "result": result,
                "source_url": profile_url
            }
            
        except Exception as e:
            logger.error(f"Profile KG extraction failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "source_url": profile_url
            }
    
    async def process_page(
        self,
        markdown_path: Path,
        page_url: str,
        page_title: str
    ) -> Dict[str, Any]:
        """
        Process a webpage markdown file through the KG pipeline
        
        Args:
            markdown_path: Path to the markdown file
            page_url: URL of the page
            page_title: Title of the page
            
        Returns:
            Dictionary with extraction results
        """
        if not self.llm:
            logger.warning("No LLM configured for KG pipeline, skipping page extraction")
            return {"status": "skipped", "reason": "no_llm"}
        
        try:
            logger.info(f"🧠 Running KG pipeline for page: {page_title}")
            
            kg_builder = SimpleKGPipeline(
                llm=self.llm,
                driver=self.driver,
                embedder=self.embedder,
                from_pdf=False,  # We're processing markdown text
                entities=PAGE_ENTITIES,
                relations=PAGE_RELATIONS,
            )
            
            # Run the pipeline
            result = await kg_builder.run_async(file_path=str(markdown_path))
            
            logger.info(f"✓ Page KG extraction complete")
            
            # Tag extracted nodes with source URL and title
            self._tag_nodes_with_source(page_url, "page", page_title)
            
            return {
                "status": "success",
                "result": result,
                "source_url": page_url,
                "title": page_title
            }
            
        except Exception as e:
            logger.error(f"Page KG extraction failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "source_url": page_url
            }
    
    def _tag_nodes_with_source(
        self,
        source_url: str,
        source_type: str,
        title: Optional[str] = None
    ):
        """
        Tag recently created nodes with source metadata
        This helps track which nodes came from which source
        """
        try:
            with self.driver.session() as session:
                # Find nodes created in the last minute and tag them
                query = """
                MATCH (n)
                WHERE n.created_at IS NULL OR datetime(n.created_at) > datetime() - duration('PT1M')
                SET n.source_url = $source_url,
                    n.source_type = $source_type,
                    n.source_title = $title,
                    n.created_at = coalesce(n.created_at, datetime())
                RETURN count(n) as tagged_count
                """
                result = session.run(query, source_url=source_url, source_type=source_type, title=title)
                record = result.single()
                if record:
                    logger.info(f"   → Tagged {record['tagged_count']} nodes with source: {source_url}")
        except Exception as e:
            logger.warning(f"Failed to tag nodes with source: {e}")

