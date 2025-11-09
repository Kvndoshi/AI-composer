"""SuperMemory service for conversation and profile storage.

This replaces Neo4j for storing conversations and profiles.
Reference: portfolio.py for SuperMemory v3 API usage.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class SuperMemoryService:
    """Service for interacting with SuperMemory API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        container: str = "ai-composer",
        base_url: str = "https://api.supermemory.ai/v3"
    ):
        """Initialize SuperMemory service.
        
        Args:
            api_key: SuperMemory API key (defaults to env var)
            container: Container tag for organizing memories
            base_url: SuperMemory API base URL
        """
        self.api_key = api_key or os.getenv("SUPERMEMORY_API_KEY")
        self.container = container
        self.base_url = base_url
        
        if not self.api_key:
            logger.warning("SuperMemory API key not set. Set SUPERMEMORY_API_KEY environment variable.")
    
    def _headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> bool:
        """Test if SuperMemory connection is working."""
        if not self.api_key:
            return False
        try:
            # Try a simple search to test connection
            response = requests.post(
                f"{self.base_url}/search",
                headers=self._headers(),
                json={"q": "test", "limit": 1, "containerTags": [self.container]},
                timeout=5
            )
            return response.status_code in (200, 201)
        except Exception as e:
            logger.error(f"SuperMemory connection test failed: {e}")
            return False
    
    def store_message(
        self,
        platform: str,
        recipient: str,
        message: str,
        is_outgoing: bool,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store a conversation message in SuperMemory.
        
        Args:
            platform: Platform (linkedin/gmail)
            recipient: Recipient name/identifier
            message: Message content
            is_outgoing: True if sent by user, False if received
            timestamp: ISO timestamp (defaults to now)
            
        Returns:
            Response from SuperMemory API
        """
        if not self.api_key:
            raise RuntimeError("SuperMemory API key not configured")
        
        timestamp = timestamp or datetime.utcnow().isoformat()
        
        # Structure the message for storage
        content = f"""
Conversation Message
Platform: {platform}
Recipient: {recipient}
Direction: {"Outgoing" if is_outgoing else "Incoming"}
Timestamp: {timestamp}

Message:
{message}
"""
        
        payload = {
            "content": content.strip(),
            "metadata": {
                "type": "conversation",
                "platform": platform,
                "recipient": recipient,
                "is_outgoing": is_outgoing,
                "timestamp": timestamp
            },
            "containerTags": [self.container]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/documents",
                headers=self._headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            doc_id = result.get("document", {}).get("id", "unknown")
            logger.info(f"✓ Stored message in SuperMemory: {doc_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to store message in SuperMemory: {e}")
            raise
    
    def get_conversation_history(
        self,
        recipient: str,
        platform: str = "linkedin",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a recipient.
        
        Args:
            recipient: Recipient name/identifier
            platform: Platform filter
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        if not self.api_key:
            logger.warning("SuperMemory API key not configured")
            return []
        
        # Search for conversations with this recipient
        query = f"conversation {recipient} {platform}"
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=self._headers(),
                json={
                    "q": query,
                    "limit": limit,
                    "containerTags": [self.container],
                    "includeFullDocs": True
                },
                timeout=30
            )
            response.raise_for_status()
            
            results = response.json().get("results", [])
            
            # Filter and format results
            messages = []
            for item in results:
                metadata = item.get("metadata", {})
                
                # Only include conversation type messages for this recipient
                if (metadata.get("type") == "conversation" and 
                    metadata.get("recipient") == recipient and
                    metadata.get("platform") == platform):
                    
                    # Extract message from content
                    content = item.get("content", "")
                    message_text = content.split("Message:")[-1].strip() if "Message:" in content else content
                    
                    messages.append({
                        "message": message_text,
                        "is_outgoing": metadata.get("is_outgoing", False),
                        "timestamp": metadata.get("timestamp", ""),
                        "platform": metadata.get("platform", platform)
                    })
            
            # Sort by timestamp (most recent first)
            messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            logger.info(f"Retrieved {len(messages)} messages for {recipient}")
            return messages[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    def search_knowledge(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search all knowledge (conversations + profiles) in SuperMemory.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        if not self.api_key:
            logger.warning("SuperMemory API key not configured")
            return []
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=self._headers(),
                json={
                    "q": query,
                    "limit": limit,
                    "containerTags": [self.container],
                    "includeFullDocs": True
                },
                timeout=30
            )
            response.raise_for_status()
            
            results = response.json().get("results", [])
            logger.info(f"Found {len(results)} results for query: {query}")
            
            return results
            
        except Exception as e:
            logger.error(f"SuperMemory search failed: {e}")
            return []
    
    def get_knowledge_snippets(
        self,
        platform: Optional[str] = None,
        recipient: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get knowledge snippets for chat context.
        
        Args:
            platform: Optional platform filter
            recipient: Optional recipient filter
            limit: Maximum results per category
            
        Returns:
            Dictionary with 'messages' and 'profiles' lists
        """
        # Build search query
        query_parts = []
        if recipient:
            query_parts.append(recipient)
        if platform:
            query_parts.append(platform)
        
        query = " ".join(query_parts) if query_parts else "recent"
        
        results = self.search_knowledge(query, limit=limit * 2)
        
        messages = []
        profiles = []
        
        for item in results:
            metadata = item.get("metadata", {})
            item_type = metadata.get("type", "")
            
            if item_type == "conversation":
                content = item.get("content", "")
                message_text = content.split("Message:")[-1].strip() if "Message:" in content else content
                
                messages.append({
                    "message": message_text,
                    "is_outgoing": metadata.get("is_outgoing", False),
                    "timestamp": metadata.get("timestamp", "")
                })
            elif item_type == "profile" or "profile" in item.get("content", "").lower():
                profiles.append({
                    "url": metadata.get("url", ""),
                    "platform": metadata.get("platform", ""),
                    "data": metadata,
                    "content": item.get("content", "")[:200]  # First 200 chars
                })
        
        return {
            "messages": messages[:limit],
            "profiles": profiles[:limit]
        }

