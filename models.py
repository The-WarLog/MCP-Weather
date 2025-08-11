#!/usr/bin/env python3
"""
Data models for the MCP Chatbot Server
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import re

# Input validation patterns
QUERY_MAX_LEN = 500
MESSAGE_MAX_LEN = 2000
SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9 \-.,'\"?!@#$%^&*()_+=\[\]{}|\\:;/<>~`\n\r\t]+$")

@dataclass
class ChatRequest:
    message: str
    context: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7

@dataclass
class ChatResponse:
    ok: bool
    response: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    detail: Optional[str] = None

@dataclass
class SearchResult:
    title: str
    snippet: str
    url: str

@dataclass
class SearchResponse:
    ok: bool
    results: List[SearchResult] = field(default_factory=list)
    query: Optional[str] = None
    error: Optional[str] = None
    detail: Optional[str] = None

@dataclass
class ServerConfig:
    # Required fields first
    openweather_api_key: str
    gemini_api_key: str
    
    # Optional fields with defaults
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5/weather"
    gemini_model: str = "gemini-2.0-flash-exp"
    search_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    search_timeout: int = 10
    search_max_results: int = 10
    log_level: str = "INFO"
    log_file: str = "puch_chatbot.log"

def validate_message(message: str) -> Optional[str]:
    """Validate chat message input"""
    if not isinstance(message, str):
        return "Message must be a string."
    
    message = message.strip()
    if not message:
        return "Message cannot be empty."
    
    if len(message) > MESSAGE_MAX_LEN:
        return f"Message too long (max {MESSAGE_MAX_LEN} chars)."
    
    return None

def validate_search_query(query: str) -> Optional[str]:
    """Validate search query input"""
    if not isinstance(query, str):
        return "Query must be a string."
    
    query = query.strip()
    if not query:
        return "Query cannot be empty."
    
    if len(query) > QUERY_MAX_LEN:
        return f"Query too long (max {QUERY_MAX_LEN} chars)."
    
    return None

def sanitize_text(text: str) -> str:
    """Basic text sanitization"""
    if not text:
        return ""
    
    # Remove any potentially harmful characters while preserving readability
    sanitized = re.sub(r'[<>]', '', text)
    return sanitized.strip()