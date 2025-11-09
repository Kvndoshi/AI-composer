"""
LLM service for message rewriting
Supports OpenAI and Anthropic models
"""

from typing import Optional
import openai
import anthropic
import asyncio
import logging
import time
import json

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, openai_key: Optional[str] = None, anthropic_key: Optional[str] = None):
        self.openai_key = openai_key
        self.anthropic_key = anthropic_key
        
        if openai_key:
            openai.api_key = openai_key
        
        if anthropic_key:
            self.anthropic_client = anthropic.Client(api_key=anthropic_key)
        else:
            self.anthropic_client = None
    
    def is_available(self) -> bool:
        """Check if at least one LLM provider is configured"""
        return bool(self.openai_key or self.anthropic_key)
    
    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name to handle common variations"""
        model_lower = model.lower()

        if model_lower == "fallback":
            return "fallback"
        if "claude-sonnet-4" in model_lower:
            return "claude-sonnet-4-5-20250929"
        
        # Handle Claude model variations
        if "claude" in model_lower:
            if "opus" in model_lower:
                return "claude-3-opus-20240229"
            elif "sonnet" in model_lower:
                return "claude-3-sonnet-20240229"
            elif "haiku" in model_lower:
                return "claude-3-haiku-20240307"
            else:
                # Default to haiku (fastest) if just "claude" is specified
                return "claude-3-haiku-20240307"
        
        # Return as-is for other models
        return model
    
    async def rewrite_message(
        self,
        user_input: str,
        context: str,
        tone: str = "professional",
        platform: str = "linkedin",
        model: str = "gpt-4",
        recipient: str = ""
    ) -> str:
        """
        Rewrite a message using the specified LLM model
        """
        if not user_input.strip():
            return ""

        if not self.is_available():
            logger.warning("No LLM provider configured. Falling back to deterministic rewrite.")
            return self._fallback_rewrite(user_input, tone, platform, context)
        
        # Normalize model name
        normalized_model = self._normalize_model_name(model)
        if normalized_model != model:
            logger.info(f"   → Model name normalized: '{model}' → '{normalized_model}'")
        model = normalized_model

        if model == "fallback":
            return self._fallback_rewrite(user_input, tone, platform, context)
        
        # Build prompt
        prompt = self._build_prompt(user_input, context, tone, platform, recipient)
        
        try:
            # Route to appropriate provider
            if model.startswith("gpt") or model.startswith("o1"):
                if not self.openai_key:
                    raise Exception("OpenAI API key not configured")
                return await self._rewrite_with_openai(prompt, model)
            elif model.startswith("claude"):
                if not self.anthropic_client:
                    raise Exception("Anthropic API key not configured")
                return await self._rewrite_with_anthropic(prompt, model)
            else:
                raise Exception(f"Unsupported model: {model}")
        except Exception as e:
            logger.error("LLM provider failed, using fallback rewrite", exc_info=True)
            return self._fallback_rewrite(user_input, tone, platform, context)
    
    def _build_prompt(self, user_input: str, context: str, tone: str, platform: str, recipient: str = "") -> str:
        """Build the prompt for message rewriting"""
        
        # Platform-specific instructions
        if platform == "linkedin":
            platform_instruction = """Rewrite this as a casual, conversational LinkedIn message.
- Keep it short and natural (2-3 sentences max)
- Use a friendly, networking tone (not formal business)
- NO greetings like "Dear" or closings like "Best regards, Sincerely"
- Just write the message content itself
- If you know the recipient's name from context, use it naturally"""
        elif platform == "gmail":
            platform_instruction = """Rewrite this as a polite, professional email.
- Keep it concise and clear
- Maintain a warm but professional tone
- NO stiff closings like "Sincerely" or "Best regards"
- Just write the message content itself
- If you know the recipient's name from context, use it naturally"""
        else:
            platform_instruction = "Rewrite this message to be clear and natural."

        # Add recipient info if available
        recipient_info = ""
        if recipient and recipient.strip() and recipient != "LinkedIn Contact" and recipient != "Email Recipient":
            recipient_info = f"\nRecipient: {recipient}"

        # Add context if available
        context_section = ""
        if context and context.strip():
            context_section = f"\nPrevious conversation context:\n{context}\n"

        prompt = f"""{platform_instruction}{recipient_info}{context_section}

User's draft:
{user_input}

Rewritten message (ONLY the message content, no extra notes or suggestions):"""

        logger.info("   → Prompt being sent to LLM:")
        logger.info("   " + "-" * 50)
        for line in prompt.split('\n'):
            logger.info(f"   {line}")
        logger.info("   " + "-" * 50)

        return prompt
    
    async def _rewrite_with_openai(self, prompt: str, model: str) -> str:
        """Rewrite using OpenAI API"""
        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a writing assistant. Rewrite the user's message EXACTLY as requested. Output ONLY the rewritten message - no explanations, no notes, no suggestions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            return self._clean_response(result)
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def _rewrite_with_anthropic(self, prompt: str, model: str) -> str:
        """Rewrite using Anthropic Claude API"""
        api_start = time.time()
        logger.info(f"   → Sending request to Anthropic API (model: {model})...")
        logger.info(f"   → Prompt length: {len(prompt)} characters")
        
        # Use faster model if Sonnet is selected (Haiku is much faster)
        if "sonnet" in model.lower():
            # Suggest Haiku for faster responses, but allow override
            logger.info(f"   → Tip: Using 'claude-3-haiku' would be 3-5x faster")
        
        try:
            api_call_start = time.time()
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=model,
                max_tokens=300,  # Reduced from 500 for faster responses
                temperature=0.3,  # Lower temperature for faster, more consistent responses
                system="You are a writing assistant. Rewrite the user's message EXACTLY as requested. Output ONLY the rewritten message - no explanations, no notes, no suggestions, no extra formatting.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            api_call_time = time.time() - api_call_start
            logger.info(f"   → API call completed in {api_call_time:.2f}s")
            
            result = response.content[0].text.strip()
            total_time = time.time() - api_start
            logger.info(f"   → Response length: {len(result)} characters")
            logger.info(f"   → Total LLM processing time: {total_time:.2f}s")
            
            return self._clean_response(result)
            
        except Exception as e:
            error_time = time.time() - api_start
            logger.error(f"   → API call failed after {error_time:.2f}s")
            logger.error(f"   → Error: {str(e)}")
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _clean_response(self, response: str) -> str:
        """Clean LLM response to remove extra notes, suggestions, or formatting"""
        # Remove common patterns of extra content
        lines = response.split('\n')
        cleaned_lines = []
        skip_rest = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Stop if we hit common "note" or "suggestion" sections
            if any(marker in line_lower for marker in [
                '---',
                '**note:**',
                'note:',
                'feel free to',
                'you can also',
                'suggestions:',
                'tips:',
                'remember to',
                'don\'t forget',
                'consider adding'
            ]):
                skip_rest = True
                continue
            
            if not skip_rest:
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Remove placeholder brackets like [Name], [topic], etc.
        import re
        result = re.sub(r'\[.*?\]', '', result)
        
        # Clean up extra whitespace
        result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
        result = result.strip()
        
        return result
    
    def get_available_models(self) -> list:
        """Return list of available models based on configured API keys"""
        models = []
        
        if self.openai_key:
            models.extend([
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo"
            ])
        
        if self.anthropic_key:
            models.extend([
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ])
        
        if not models:
            models.append("fallback")
        
        return models

    def _fallback_rewrite(self, user_input: str, tone: str, platform: str, context: str) -> str:
        """Deterministic rewrite when no LLM is available."""
        logger.info("   → Using fallback rewrite logic")
        text = user_input.strip()
        if not text:
            return ""

        # Basic sentence cleanup
        sentences = [s.strip().capitalize() for s in text.replace('\n', ' ').split('.')]
        sentences = [s for s in sentences if s]
        rewritten_body = '. '.join(sentences)
        if not rewritten_body:
            rewritten_body = text.capitalize()
        if rewritten_body and rewritten_body[-1] not in '.!?':
            rewritten_body += '.'

        if platform == "linkedin":
            if tone == "friendly":
                return f"Just to share heads-up: {rewritten_body}"
            return f"Following up: {rewritten_body}"
        elif platform == "gmail":
            return rewritten_body
        else:
            return rewritten_body

    async def answer_question(
        self,
        question: str,
        knowledge_context: str,
        model: str = "fallback",
        session_id: str = "default",
        page_title: Optional[str] = None,
        page_content: Optional[str] = None,
        chat_history: str = ""
    ) -> str:
        if not question.strip():
            return ""

        if not self.is_available():
            logger.warning("LLM unavailable, using fallback answer.")
            return self._fallback_answer(question, knowledge_context)

        normalized_model = self._normalize_model_name(model)
        
        # Determine if this is summarizer mode (has page_content) or regular chat
        is_summarizer = bool(page_content and page_title)
        mode = "summarizer" if is_summarizer else "chat"
        logger.info(f"   → {mode.capitalize()} model selected: {normalized_model}")

        if normalized_model == "fallback":
            return self._fallback_answer(question, knowledge_context)

        # Build appropriate prompt based on mode
        if is_summarizer:
            prompt = self._build_summarizer_prompt(question, page_content, page_title, chat_history)
        else:
            prompt = self._build_chat_prompt(question, knowledge_context, session_id)

        try:
            if normalized_model.startswith("gpt") or normalized_model.startswith("o1"):
                if not self.openai_key:
                    raise Exception("OpenAI API key not configured")
                return await self._rewrite_with_openai(prompt, normalized_model)
            elif normalized_model.startswith("claude"):
                if not self.anthropic_client:
                    raise Exception("Anthropic API key not configured")
                return await self._rewrite_with_anthropic(prompt, normalized_model)
            else:
                raise Exception(f"Unsupported model: {normalized_model}")
        except Exception:
            logger.error(f"{mode.capitalize()} LLM call failed; using fallback answer.", exc_info=True)
            return self._fallback_answer(question, knowledge_context)

    async def extract_profile(
        self,
        profile_data: dict,
        model: str = "fallback"
    ) -> dict:
        combined_text = self._compose_profile_text(profile_data)
        if not combined_text.strip():
            return self._fallback_profile_structure(profile_data, combined_text)

        normalized_model = self._normalize_model_name(model)
        if not self.is_available() or normalized_model == "fallback":
            return self._fallback_profile_structure(profile_data, combined_text)

        prompt = self._build_profile_prompt(combined_text)

        try:
            if normalized_model.startswith("gpt") or normalized_model.startswith("o1"):
                if not self.openai_key:
                    raise Exception("OpenAI API key not configured")
                response = await self._rewrite_with_openai(prompt, normalized_model)
            elif normalized_model.startswith("claude"):
                if not self.anthropic_client:
                    raise Exception("Anthropic API key not configured")
                response = await self._rewrite_with_anthropic(prompt, normalized_model)
            else:
                raise Exception(f"Unsupported model: {normalized_model}")

            structured = self._parse_profile_json(response, profile_data, combined_text)
        except Exception:
            logger.error("Profile extraction failed; using fallback structure.", exc_info=True)
            structured = self._fallback_profile_structure(profile_data, combined_text)

        structured.setdefault("raw_text", combined_text)
        return structured

    def _build_chat_prompt(self, question: str, knowledge_context: str, session_id: str = "default") -> str:
        """Build prompt for general knowledge graph chat"""
        prompt = """You are a highly personalized AI assistant. Your primary goal is to learn about the user and provide increasingly personalized help over time.

MEMORY MANAGEMENT:
1. When users share personal information, preferences, or context, immediately store it
2. Before responding to requests, search for relevant context about the user
3. Use past conversations to inform current responses
4. Remember user's communication style, preferences, and frequently discussed topics

PERSONALITY:
- Adapt your communication style to match the user's preferences
- Reference past conversations naturally when relevant
- Proactively offer help based on learned patterns
- Be genuinely helpful while respecting privacy
"""
        if knowledge_context:
            prompt += f"Knowledge graph snippets:\n{knowledge_context}\n\n"
        else:
            prompt += "Knowledge graph snippets: (none)\n\n"
        prompt += f"User question: {question}\n\nAnswer:"

        logger.info("   → Chat prompt being sent to LLM:")
        logger.info("   " + "-" * 50)
        for line in prompt.split("\n"):
            logger.info(f"   {line}")
        logger.info("   " + "-" * 50)

        return prompt
    
    def _build_summarizer_prompt(self, question: str, page_content: str, page_title: str, chat_history: str = "") -> str:
        """Build prompt for page summarizer mode"""
        prompt = f"""You are analyzing the webpage: "{page_title}"

Your task is to answer questions about this specific page using ONLY the content provided below.

Page Content:
{page_content[:4000]}

Guidelines:
- If asked to "summarize", provide a clear, concise overview of the main points
- If asked a specific question, extract and explain the relevant information
- Use bullet points for clarity when appropriate
- Be accurate and stick to what's in the content
- If the answer isn't in the page, clearly state that
- Keep responses focused and relevant
"""
        
        if chat_history:
            prompt += f"\n\nPrevious conversation:\n{chat_history}\n"
        
        prompt += f"\n\nUser's Question: {question}\n\nYour Response:"
        
        logger.info("   → Summarizer prompt being sent to LLM:")
        logger.info("   " + "-" * 50)
        for line in prompt.split("\n")[:30]:  # Show first 30 lines
            logger.info(f"   {line}")
        logger.info("   " + "-" * 50)
        
        return prompt

    def _fallback_answer(self, question: str, knowledge_context: str) -> str:
        if knowledge_context.strip():
            return (
                "Based on what I currently know:\n"
                f"{knowledge_context}\n\n"
                f"For your question \"{question}\", this is the best summary available. "
                "If you need more detail, try saving additional conversations or profiles first."
            )
        return (
            "I don't have any saved knowledge yet to answer that. "
            "Try capturing profiles or conversations, then ask again."
        )

    def _compose_profile_text(self, profile_data: dict) -> str:
        parts = []
        title = profile_data.get("title")
        if title:
            parts.append(f"Title: {title}")
        summary = profile_data.get("summary")
        if summary:
            parts.append(f"Summary: {summary}")
        snippet = profile_data.get("snippet")
        if snippet:
            parts.append(f"Snippet: {snippet}")
        return "\n".join(parts)

    def _build_profile_prompt(self, combined_text: str) -> str:
        prompt = (
            "Extract structured information about a professional contact from the text below. "
            "Return ONLY valid JSON following this schema:\n"
            "{\n"
            '  "name": string,\n'
            '  "headline": string,\n'
            '  "summary": string,\n'
            '  "location": string,\n'
            '  "company": string,\n'
            '  "title": string,\n'
            '  "experiences": [\n'
            '    {"role": string, "company": string, "start_date": string, "end_date": string, "location": string, "description": string}\n'
            "  ],\n"
            '  "education": [\n'
            '    {"school": string, "degree": string, "field": string, "start_date": string, "end_date": string}\n'
            "  ],\n"
            '  "skills": [string]\n'
            "}\n"
            "If a field is unknown, use an empty string or empty array. "
            "Do not include additional commentary.\n\n"
            f"Text:\n{combined_text}\n\n"
            "JSON:"
        )
        logger.info("   → Profile extraction prompt:")
        logger.info("   " + "-" * 50)
        for line in prompt.split("\n"):
            logger.info(f"   {line}")
        logger.info("   " + "-" * 50)
        return prompt

    def _parse_profile_json(self, response_text: str, original_data: dict, combined_text: str) -> dict:
        try:
            json_text = response_text.strip()
            if json_text.startswith("```"):
                json_text = json_text.strip("`")
                if "\n" in json_text:
                    json_text = json_text.split("\n", 1)[1]
            data = json.loads(json_text)
        except Exception:
            logger.error("Failed to parse profile JSON", exc_info=True)
            return self._fallback_profile_structure(original_data, combined_text)

        if not isinstance(data, dict):
            return self._fallback_profile_structure(original_data, combined_text)

        data.setdefault("experiences", [])
        data.setdefault("education", [])
        data.setdefault("skills", [])
        data.setdefault("summary", original_data.get("summary") or "")
        data.setdefault("headline", original_data.get("title") or "")
        return data

    def _fallback_profile_structure(self, profile_data: dict, combined_text: str) -> dict:
        title = profile_data.get("title", "")
        parts = [p.strip() for p in title.split("|")] if title else []
        name = parts[0] if parts else ""
        remainder = parts[1] if len(parts) > 1 else profile_data.get("summary", "")

        return {
            "name": name,
            "headline": remainder,
            "summary": profile_data.get("summary", ""),
            "location": "",
            "company": "",
            "title": remainder,
            "experiences": [],
            "education": [],
            "skills": [],
            "raw_text": combined_text or profile_data.get("snippet", "")
        }

