"""
Neo4j service for storing and retrieving conversation history
Uses a graph structure to maintain relationships between users and messages
"""

from neo4j import GraphDatabase
from typing import List, Dict, Optional
from datetime import datetime


class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        """Close the Neo4j driver connection"""
        self.driver.close()
    
    def test_connection(self) -> bool:
        """Test if Neo4j connection is working"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                return result.single()[0] == 1
        except Exception as e:
            print(f"Neo4j connection error: {e}")
            return False
    
    def initialize_schema(self):
        """Create indexes and constraints for better performance"""
        with self.driver.session() as session:
            # Create constraints
            session.run("""
                CREATE CONSTRAINT user_id IF NOT EXISTS
                FOR (u:User) REQUIRE u.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT message_id IF NOT EXISTS
                FOR (m:Message) REQUIRE m.id IS UNIQUE
            """)
            
            # Create indexes
            session.run("""
                CREATE INDEX user_platform IF NOT EXISTS
                FOR (u:User) ON (u.platform)
            """)
            
            session.run("""
                CREATE INDEX message_timestamp IF NOT EXISTS
                FOR (m:Message) ON (m.timestamp)
            """)
    
    def store_message(
        self,
        platform: str,
        recipient: str,
        message: str,
        is_outgoing: bool,
        timestamp: str
    ):
        """
        Store a message in Neo4j graph
        Creates User nodes and Message nodes with relationships
        """
        with self.driver.session() as session:
            session.execute_write(
                self._create_message_tx,
                platform,
                recipient,
                message,
                is_outgoing,
                timestamp
            )
    
    @staticmethod
    def _create_message_tx(tx, platform, recipient, message, is_outgoing, timestamp):
        """Transaction function to create message and relationships"""
        
        # Create or merge user node
        tx.run("""
            MERGE (u:User {id: $recipient, platform: $platform})
            ON CREATE SET u.created_at = datetime()
            SET u.last_interaction = datetime()
        """, recipient=recipient, platform=platform)
        
        # Create message node
        message_id = f"{platform}_{recipient}_{timestamp}"
        tx.run("""
            CREATE (m:Message {
                id: $message_id,
                text: $message,
                is_outgoing: $is_outgoing,
                timestamp: datetime($timestamp),
                platform: $platform
            })
        """, message_id=message_id, message=message, is_outgoing=is_outgoing, 
             timestamp=timestamp, platform=platform)
        
        # Create relationship
        if is_outgoing:
            tx.run("""
                MATCH (u:User {id: $recipient, platform: $platform})
                MATCH (m:Message {id: $message_id})
                CREATE (u)<-[:SENT_TO]-(m)
            """, recipient=recipient, platform=platform, message_id=message_id)
        else:
            tx.run("""
                MATCH (u:User {id: $recipient, platform: $platform})
                MATCH (m:Message {id: $message_id})
                CREATE (u)-[:SENT]->(m)
            """, recipient=recipient, platform=platform, message_id=message_id)
    
    def get_conversation_history(
        self,
        recipient: str,
        platform: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve conversation history with a recipient
        Returns messages ordered by timestamp
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._get_conversation_tx,
                recipient,
                platform,
                limit
            )
            return result
    
    @staticmethod
    def _get_conversation_tx(tx, recipient, platform, limit):
        """Transaction function to retrieve conversation history"""
        result = tx.run("""
            MATCH (u:User {id: $recipient, platform: $platform})
            MATCH (m:Message {platform: $platform})
            WHERE (u)<-[:SENT_TO]-(m) OR (u)-[:SENT]->(m)
            RETURN m.text as message, 
                   m.is_outgoing as is_outgoing,
                   m.timestamp as timestamp
            ORDER BY m.timestamp DESC
            LIMIT $limit
        """, recipient=recipient, platform=platform, limit=limit)
        
        messages = []
        for record in result:
            messages.append({
                "message": record["message"],
                "is_outgoing": record["is_outgoing"],
                "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None
            })
        
        # Return in chronological order (oldest first)
        return list(reversed(messages))
    
    def get_related_conversations(
        self,
        recipient: str,
        platform: str,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Get related conversations based on graph relationships
        This can be extended to use embeddings for semantic search
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._get_related_conversations_tx,
                recipient,
                platform
            )
            return result
    
    @staticmethod
    def _get_related_conversations_tx(tx, recipient, platform):
        """Get conversations with similar patterns or topics"""
        # For now, return recent messages from the same platform
        # This can be enhanced with semantic similarity
        result = tx.run("""
            MATCH (u:User {id: $recipient, platform: $platform})
            MATCH (m:Message {platform: $platform})
            WHERE (u)<-[:SENT_TO]-(m) OR (u)-[:SENT]->(m)
            RETURN m.text as message,
                   m.is_outgoing as is_outgoing,
                   m.timestamp as timestamp
            ORDER BY m.timestamp DESC
            LIMIT 5
        """, recipient=recipient, platform=platform)
        
        messages = []
        for record in result:
            messages.append({
                "message": record["message"],
                "is_outgoing": record["is_outgoing"],
                "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None
            })
        
        return messages
    
    def delete_conversation_history(self, recipient: str, platform: str):
        """Delete all messages for a specific recipient"""
        with self.driver.session() as session:
            session.execute_write(
                self._delete_conversation_tx,
                recipient,
                platform
            )
    
    @staticmethod
    def _delete_conversation_tx(tx, recipient, platform):
        """Transaction to delete conversation history"""
        tx.run("""
            MATCH (u:User {id: $recipient, platform: $platform})
            MATCH (m:Message {platform: $platform})
            WHERE (u)<-[:SENT_TO]-(m) OR (u)-[:SENT]->(m)
            DETACH DELETE m
        """, recipient=recipient, platform=platform)
    
    def get_user_stats(self, recipient: str, platform: str) -> Dict:
        """Get statistics about conversations with a user"""
        with self.driver.session() as session:
            result = session.execute_read(
                self._get_user_stats_tx,
                recipient,
                platform
            )
            return result
    
    @staticmethod
    def _get_user_stats_tx(tx, recipient, platform):
        """Get conversation statistics"""
        result = tx.run("""
            MATCH (u:User {id: $recipient, platform: $platform})
            MATCH (m:Message {platform: $platform})
            WHERE (u)<-[:SENT_TO]-(m) OR (u)-[:SENT]->(m)
            RETURN count(m) as total_messages,
                   sum(CASE WHEN m.is_outgoing THEN 1 ELSE 0 END) as outgoing_count,
                   sum(CASE WHEN NOT m.is_outgoing THEN 1 ELSE 0 END) as incoming_count,
                   max(m.timestamp) as last_message
        """, recipient=recipient, platform=platform)
        
        record = result.single()
        if record:
            return {
                "total_messages": record["total_messages"],
                "outgoing_count": record["outgoing_count"],
                "incoming_count": record["incoming_count"],
                "last_message": record["last_message"].isoformat() if record["last_message"] else None
            }
        
        return {
            "total_messages": 0,
            "outgoing_count": 0,
            "incoming_count": 0,
            "last_message": None
        }

    def store_profile(self, platform: str, profile_url: str, profile_data: dict):
        with self.driver.session() as session:
            session.execute_write(
                self._store_profile_tx,
                platform,
                profile_url,
                profile_data
            )

    @staticmethod
    def _store_profile_tx(tx, platform, profile_url, profile_data):
        raw_text = profile_data.get("raw_text", "")

        simple_props = {
            k: v for k, v in profile_data.items()
            if k not in ("experiences", "education", "skills", "raw_text")
            and isinstance(v, (str, int, float, bool))
        }

        tx.run(
            """
            MERGE (p:Profile {url: $profile_url, platform: $platform})
            SET p += $props,
                p.raw_text = $raw_text,
                p.last_scraped = datetime()
            """,
            profile_url=profile_url,
            platform=platform,
            props=simple_props,
            raw_text=raw_text
        )

        # Clear previous relationships
        tx.run("""
            MATCH (p:Profile {url:$profile_url, platform:$platform})-[r:HAS_EXPERIENCE]->(e:Experience)
            DETACH DELETE e
        """, profile_url=profile_url, platform=platform)

        tx.run("""
            MATCH (p:Profile {url:$profile_url, platform:$platform})-[r:HAS_EDUCATION]->(e:Education)
            DETACH DELETE e
        """, profile_url=profile_url, platform=platform)

        tx.run("""
            MATCH (p:Profile {url:$profile_url, platform:$platform})-[r:HAS_SKILL]->(:Skill)
            DELETE r
        """, profile_url=profile_url, platform=platform)

        experiences = profile_data.get("experiences") or []
        for idx, exp in enumerate(experiences):
            if not isinstance(exp, dict):
                continue
            exp_props = {k: v for k, v in exp.items() if v and isinstance(v, (str, int, float, bool))}
            exp_props["index"] = idx
            exp_id = f"{profile_url}#experience#{idx}"
            tx.run(
                """
                MATCH (p:Profile {url:$profile_url, platform:$platform})
                MERGE (e:Experience {id:$exp_id})
                SET e += $exp_props
                MERGE (p)-[:HAS_EXPERIENCE]->(e)
                """,
                profile_url=profile_url,
                platform=platform,
                exp_id=exp_id,
                exp_props=exp_props
            )

        education_list = profile_data.get("education") or []
        for idx, edu in enumerate(education_list):
            if not isinstance(edu, dict):
                continue
            edu_props = {k: v for k, v in edu.items() if v and isinstance(v, (str, int, float, bool))}
            edu_props["index"] = idx
            edu_id = f"{profile_url}#education#{idx}"
            tx.run(
                """
                MATCH (p:Profile {url:$profile_url, platform:$platform})
                MERGE (e:Education {id:$edu_id})
                SET e += $edu_props
                MERGE (p)-[:HAS_EDUCATION]->(e)
                """,
                profile_url=profile_url,
                platform=platform,
                edu_id=edu_id,
                edu_props=edu_props
            )

        skills = profile_data.get("skills") or []
        for skill in skills:
            if not skill or not isinstance(skill, str):
                continue
            tx.run(
                """
                MATCH (p:Profile {url:$profile_url, platform:$platform})
                MERGE (s:Skill {name:$skill})
                MERGE (p)-[:HAS_SKILL]->(s)
                """,
                profile_url=profile_url,
                platform=platform,
                skill=skill.strip()
            )

    def get_knowledge_snippets(self, platform: Optional[str] = None, recipient: Optional[str] = None, limit: int = 5) -> Dict[str, List[Dict]]:
        """Gather recent knowledge graph snippets for chat context."""
        with self.driver.session() as session:
            conversations = session.execute_read(
                self._get_recent_messages_tx,
                platform,
                recipient,
                limit
            )
            profiles = session.execute_read(
                self._get_recent_profiles_tx,
                platform,
                limit
            )
            return {
                "messages": conversations,
                "profiles": profiles
            }

    @staticmethod
    def _get_recent_messages_tx(tx, platform, recipient, limit):
        query = [
            "MATCH (m:Message)",
        ]
        where_clauses = []
        params = {"limit": limit}
        if platform:
            where_clauses.append("m.platform = $platform")
            params["platform"] = platform
        if recipient:
            query.append("MATCH (u:User {id: $recipient})")
            query.append("WHERE (u)<-[:SENT_TO]-(m) OR (u)-[:SENT]->(m)")
            params["recipient"] = recipient
        elif where_clauses:
            query.append("WHERE " + " AND ".join(where_clauses))
        query.append("RETURN m.text AS message, m.is_outgoing AS is_outgoing, m.timestamp AS timestamp, m.platform AS platform")
        query.append("ORDER BY m.timestamp DESC")
        query.append("LIMIT $limit")
        result = tx.run("\n".join(query), **params)
        data = []
        for record in result:
            data.append({
                "message": record["message"],
                "is_outgoing": record["is_outgoing"],
                "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None,
                "platform": record["platform"]
            })
        return data

    @staticmethod
    def _get_recent_profiles_tx(tx, platform, limit):
        params = {"limit": limit}
        where_clause = ""
        if platform:
            where_clause = "WHERE p.platform = $platform"
            params["platform"] = platform
        
        # Query both Profile and ScrapedProfile nodes
        result = tx.run(
            f"""
            CALL {{
                MATCH (p:Profile)
                {where_clause}
                RETURN p.url AS url, p.platform AS platform, p.updated_at AS timestamp, 
                       p AS node, p.content AS content
                UNION
                MATCH (p:ScrapedProfile)
                {where_clause}
                RETURN p.url AS url, p.platform AS platform, p.scraped_at AS timestamp,
                       p AS node, p.content AS content
            }}
            RETURN url, platform, node, content
            ORDER BY timestamp DESC
            LIMIT $limit
            """,
            **params
        )
        profiles = []
        for record in result:
            node_props = dict(record["node"])
            # Extract key fields
            url = record["url"]
            platform = record["platform"]
            content = record.get("content", "")
            
            # Remove redundant fields
            node_props.pop("url", None)
            node_props.pop("platform", None)
            node_props.pop("content", None)
            
            profiles.append({
                "url": url,
                "platform": platform,
                "data": node_props,
                "content": content[:500] if content else ""  # First 500 chars
            })
        return profiles
    
    def store_scraped_profile(self, url: str, platform: str, markdown_content: str):
        """Store scraped profile data as unstructured text in Neo4j.
        
        Args:
            url: Profile URL
            platform: Platform (linkedin/gmail)
            markdown_content: Full markdown content from scraping
        """
        with self.driver.session() as session:
            session.run(
                """
                MERGE (p:ScrapedProfile {url: $url, platform: $platform})
                SET p.content = $content,
                    p.scraped_at = datetime(),
                    p.content_length = size($content)
                RETURN p
                """,
                url=url,
                platform=platform,
                content=markdown_content
            )
    
    def store_chat_message(self, role: str, message: str, session_id: str = "default"):
        """Store a chat message for the assistant's memory.
        
        Args:
            role: 'user' or 'assistant'
            message: The message content
            session_id: Chat session identifier (default: "default")
        """
        with self.driver.session() as session:
            session.run(
                """
                CREATE (m:ChatMessage {
                    role: $role,
                    message: $message,
                    session_id: $session_id,
                    timestamp: datetime()
                })
                RETURN m
                """,
                role=role,
                message=message,
                session_id=session_id
            )
    
    def get_chat_history(self, session_id: str = "default", limit: int = 20):
        """Retrieve chat history for assistant memory.
        
        Args:
            session_id: Chat session identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of chat messages in chronological order
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (m:ChatMessage {session_id: $session_id})
                RETURN m.role as role, m.message as message, m.timestamp as timestamp
                ORDER BY m.timestamp ASC
                LIMIT $limit
                """,
                session_id=session_id,
                limit=limit
            )
            
            messages = []
            for record in result:
                messages.append({
                    "role": record["role"],
                    "message": record["message"],
                    "timestamp": str(record["timestamp"])
                })
            
            return messages
    
    def clear_chat_history(self, session_id: str = "default"):
        """Clear chat history for a session.
        
        Args:
            session_id: Chat session identifier
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (m:ChatMessage {session_id: $session_id})
                DELETE m
                """,
                session_id=session_id
            )
    
    def store_page_summary(self, url: str, title: str, content: str):
        """Store a scraped page for summarization and Q&A.
        
        Args:
            url: Page URL (used as unique identifier)
            title: Page title
            content: Full page content (markdown)
        """
        with self.driver.session() as session:
            session.run(
                """
                MERGE (p:PageSummary {url: $url})
                SET p.title = $title,
                    p.content = $content,
                    p.scraped_at = datetime(),
                    p.content_length = size($content)
                RETURN p
                """,
                url=url,
                title=title,
                content=content
            )
    
    def get_page_summary(self, url: str):
        """Retrieve a stored page by URL.
        
        Args:
            url: Page URL
            
        Returns:
            Dictionary with page data or None if not found
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:PageSummary {url: $url})
                RETURN p.title as title, 
                       p.content as content, 
                       p.scraped_at as scraped_at,
                       p.content_length as content_length
                LIMIT 1
                """,
                url=url
            )
            
            record = result.single()
            if record:
                return {
                    "url": url,
                    "title": record["title"],
                    "content": record["content"],
                    "scraped_at": str(record["scraped_at"]),
                    "content_length": record["content_length"]
                }
            return None
    
    def search_pages(self, query: str, limit: int = 5):
        """Search stored pages by title or URL.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching pages
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:PageSummary)
                WHERE p.title CONTAINS $query OR p.url CONTAINS $query
                RETURN p.url as url, 
                       p.title as title, 
                       p.content_length as content_length,
                       p.scraped_at as scraped_at
                ORDER BY p.scraped_at DESC
                LIMIT $limit
                """,
                query=query,
                limit=limit
            )
            
            pages = []
            for record in result:
                pages.append({
                    "url": record["url"],
                    "title": record["title"],
                    "content_length": record["content_length"],
                    "scraped_at": str(record["scraped_at"])
                })
            return pages

