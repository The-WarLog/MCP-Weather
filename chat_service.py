#!/usr/bin/env python3
"""
Chat service using Google Gemini API
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
import google.generativeai as genai
from models import ChatRequest, ChatResponse, validate_message, sanitize_text

logger = logging.getLogger("puch.chat")

class ChatService:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key
        self.model = model
        self._client: Optional[genai.GenerativeModel] = None
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the Gemini client"""
        try:
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
            logger.info(f"Gemini client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    async def process_message(self, message: str, context: Optional[str] = None) -> ChatResponse:
        """Process a chat message using Gemini API"""
        logger.info("Processing chat message", extra={"message_len": len(message)})
        
        # Validate input
        validation_error = validate_message(message)
        if validation_error:
            logger.warning("Invalid chat message", extra={"error": validation_error})
            return ChatResponse(
                ok=False,
                error="validation",
                detail=validation_error
            )
        
        # Sanitize input
        clean_message = sanitize_text(message)
        
        try:
            # Prepare the prompt
            if context:
                prompt = f"Context: {sanitize_text(context)}\n\nUser: {clean_message}"
            else:
                prompt = clean_message
            
            # Make the API call
            response = await self._make_gemini_request(prompt)
            
            return ChatResponse(
                ok=True,
                response=response.text,
                usage={"prompt_tokens": len(prompt), "completion_tokens": len(response.text)}
            )
            
        except Exception as e:
            logger.error("Error processing chat message", exc_info=True)
            return ChatResponse(
                ok=False,
                error="internal",
                detail=str(e)
            )
    
    async def _make_gemini_request(self, prompt: str):
        """Make async request to Gemini API"""
        if not self._client:
            raise RuntimeError("Gemini client not initialized")
        
        # Run the blocking Gemini call in a thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            self._client.generate_content, 
            prompt
        )
        
        return response