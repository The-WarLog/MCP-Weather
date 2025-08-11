#!/usr/bin/env python3
"""
Puch.AI MCP Chatbot Server - Working Prototype

A comprehensive MCP server with:
- Weather information (OpenWeatherMap)
- AI Chat (Gemini 2.5 Flash)
- Web Search (Google scraping, no API key needed)

Usage:
  # Set environment variables
  $env:OPENWEATHER_API_KEY = "your_openweather_key"
  $env:GEMINI_API_KEY = "your_gemini_key"
  
  # Run as MCP server
  python main.py --server
  
  # Test individual features
  python main.py --chat "Hello, how are you?"
  python main.py --search "Python programming"
  python main.py --weather "London"
"""

import os
import sys
import asyncio
import logging
import argparse
import signal
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from chat_service import ChatService
from search_service import SearchService
from models import ServerConfig

# Global variables
logger = logging.getLogger("puch.main")
shutdown_event = asyncio.Event()

def setup_logging(log_level: str = "INFO", log_file: str = "puch_chatbot.log"):
    """Setup production-ready logging"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    logger.info(f"Logging configured - Level: {log_level}, File: {log_dir / log_file}")

def setup_signal_handlers():
    """Setup graceful shutdown signal handlers"""
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Signal handlers registered for graceful shutdown")

# Initialize MCP server
mcp = FastMCP("Puch.AI Chatbot Server")

# Global services (initialized in main)
chat_service: Optional[ChatService] = None
search_service: Optional[SearchService] = None

def load_config() -> ServerConfig:
    """Load configuration from .env file and environment variables"""
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded configuration from {env_path}")
    else:
        logger.info("No .env file found, using environment variables only")
    
    # Get required API keys
    openweather_key = os.getenv("OPENWEATHER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    # Validate required configuration
    missing_vars = []
    if not openweather_key:
        missing_vars.append("OPENWEATHER_API_KEY")
    if not gemini_key:
        missing_vars.append("GEMINI_API_KEY")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Mask API keys in logs for security
    logger.info(f"OpenWeather API key loaded: {openweather_key[:8]}...")
    logger.info(f"Gemini API key loaded: {gemini_key[:8]}...")
    
    # Helper function to clean environment values (remove quotes if present)
    def clean_env_value(value, default):
        if not value:
            return default
        # Remove surrounding quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        return value
    
    return ServerConfig(
        openweather_api_key=clean_env_value(openweather_key, ""),
        gemini_api_key=clean_env_value(gemini_key, ""),
        gemini_model=clean_env_value(os.getenv("GEMINI_MODEL"), "gemini-2.0-flash-exp"),
        openweather_base_url=clean_env_value(os.getenv("OPENWEATHER_BASE_URL"), "https://api.openweathermap.org/data/2.5/weather"),
        search_user_agent=clean_env_value(os.getenv("SEARCH_USER_AGENT"), "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        search_timeout=int(clean_env_value(os.getenv("SEARCH_TIMEOUT"), "10")),
        search_max_results=int(clean_env_value(os.getenv("SEARCH_MAX_RESULTS"), "10")),
        log_level=clean_env_value(os.getenv("LOG_LEVEL"), "INFO"),
        log_file=clean_env_value(os.getenv("LOG_FILE"), "puch_chatbot.log")
    )

@mcp.tool()
async def chat(message: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Chat with AI using Gemini 2.5 Flash
    
    Args:
        message: Your message to the AI
        context: Optional conversation context
        
    Returns:
        Dict with AI response or error information
    """
    if not chat_service:
        return {"ok": False, "error": "service_unavailable", "detail": "Chat service not initialized"}
    
    response = await chat_service.process_message(message, context)
    return {
        "ok": response.ok,
        "response": response.response,
        "usage": response.usage,
        "error": response.error,
        "detail": response.detail
    }

@mcp.tool()
async def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using Google (no API key required)
    
    Args:
        query: Search query
        num_results: Number of results to return (1-10)
        
    Returns:
        Dict with search results or error information
    """
    if not search_service:
        return {"ok": False, "error": "service_unavailable", "detail": "Search service not initialized"}
    
    response = await search_service.search_google(query, num_results)
    return {
        "ok": response.ok,
        "results": [
            {
                "title": r.title,
                "snippet": r.snippet,
                "url": r.url
            } for r in response.results
        ],
        "query": response.query,
        "error": response.error,
        "detail": response.detail
    }

@mcp.tool()
async def get_weather(city: str, units: str = "metric") -> Dict[str, Any]:
    """
    Get current weather for a city
    
    Args:
        city: City name
        units: Temperature units ("metric" or "imperial")
        
    Returns:
        Dict with weather information or error
    """
    # Import the existing weather function from puch.py
    try:
        from puch import get_weather as puch_weather
        return await puch_weather(city, units)
    except ImportError:
        # Fallback simple implementation
        import httpx
        
        config = load_config()
        params = {
            "q": city,
            "appid": config.openweather_api_key,
            "units": units
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(config.openweather_base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "ok": True,
                        "city": data.get("name"),
                        "country": data.get("sys", {}).get("country"),
                        "temp": data.get("main", {}).get("temp"),
                        "feels_like": data.get("main", {}).get("feels_like"),
                        "humidity": data.get("main", {}).get("humidity"),
                        "conditions": data.get("weather", [{}])[0].get("description"),
                        "units": units
                    }
                else:
                    return {"ok": False, "error": "api_error", "detail": f"Weather API returned {response.status_code}"}
            except Exception as e:
                return {"ok": False, "error": "internal", "detail": str(e)}

async def test_chat(message: str):
    """Test chat functionality"""
    result = await chat(message)
    if result.get("ok"):
        print(f"AI: {result.get('response')}")
    else:
        print(f"Chat Error: {result.get('detail')}")

async def test_search(query: str):
    """Test search functionality"""
    result = await search_web(query, 3)
    if result.get("ok"):
        print(f"Search results for '{query}':")
        for i, r in enumerate(result.get("results", []), 1):
            print(f"{i}. {r['title']}")
            print(f"   {r['snippet']}")
            print(f"   {r['url']}\n")
    else:
        print(f"Search Error: {result.get('detail')}")

async def test_weather(city: str):
    """Test weather functionality"""
    result = await get_weather(city)
    if result.get("ok"):
        print(f"Weather in {result.get('city')}, {result.get('country')}:")
        print(f"Temperature: {result.get('temp')}°C (feels like {result.get('feels_like')}°C)")
        print(f"Conditions: {result.get('conditions')}")
        print(f"Humidity: {result.get('humidity')}%")
    else:
        print(f"Weather Error: {result.get('detail')}")

async def cleanup_services():
    """Cleanup services on shutdown"""
    global chat_service, search_service
    logger.info("Cleaning up services...")
    
    # Add any cleanup logic here
    # For example, closing HTTP clients, database connections, etc.
    
    logger.info("Services cleaned up successfully")

class ProductionMCPServer:
    """Production-ready MCP server with proper lifecycle management"""
    
    def __init__(self):
        self.server_thread = None
        self.is_running = False
        self.shutdown_requested = False
    
    def start_server_thread(self):
        """Start MCP server in a separate thread"""
        def run_mcp():
            try:
                logger.info("MCP server thread starting...")
                mcp.run()
            except Exception as e:
                logger.error(f"MCP server thread error: {e}", exc_info=True)
            finally:
                logger.info("MCP server thread stopped")
                self.is_running = False
        
        self.server_thread = threading.Thread(target=run_mcp, daemon=False)
        self.server_thread.start()
        self.is_running = True
        logger.info("MCP server thread started successfully")
    
    def stop_server(self):
        """Stop the MCP server gracefully"""
        logger.info("Stopping MCP server...")
        self.shutdown_requested = True
        
        if self.server_thread and self.server_thread.is_alive():
            # Give the server thread time to shutdown gracefully
            self.server_thread.join(timeout=5.0)
            if self.server_thread.is_alive():
                logger.warning("MCP server thread did not shutdown gracefully")
        
        self.is_running = False
        logger.info("MCP server stopped")

async def run_server():
    """Run MCP server with graceful shutdown and health monitoring"""
    logger.info("Starting production MCP server...")
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Create production server instance
    server = ProductionMCPServer()
    
    try:
        # Start the MCP server
        server.start_server_thread()
        
        logger.info("=== MCP SERVER READY ===")
        logger.info("Server is running and accepting MCP connections")
        logger.info("Available tools: chat, search_web, get_weather")
        logger.info("Press Ctrl+C to shutdown gracefully")
        logger.info("========================")
        
        # Health monitoring loop
        while server.is_running and not shutdown_event.is_set():
            await asyncio.sleep(1.0)
            
            # Log periodic health status
            if int(time.time()) % 300 == 0:  # Every 5 minutes
                logger.info("Server health check: MCP server is running")
        
        logger.info("Shutdown signal received, stopping server...")
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        # Cleanup
        server.stop_server()
        await cleanup_services()
        logger.info("=== SERVER SHUTDOWN COMPLETE ===")

async def run_persistent_server():
    """Run server in persistent mode for production deployment"""
    logger.info("Starting persistent MCP server for production deployment...")
    
    # Setup signal handlers
    setup_signal_handlers()
    
    logger.info("=== PRODUCTION MCP SERVER ===")
    logger.info("Server starting in persistent mode...")
    logger.info("This server will run continuously until stopped")
    logger.info("Available MCP tools:")
    logger.info("  - chat(message, context?) - AI chat with Gemini")
    logger.info("  - search_web(query, num_results?) - Web search")
    logger.info("  - get_weather(city, units?) - Weather information")
    logger.info("=============================")
    
    try:
        # Run the server indefinitely
        while not shutdown_event.is_set():
            try:
                # Start MCP server in executor to avoid blocking
                await asyncio.get_event_loop().run_in_executor(None, mcp.run)
            except Exception as e:
                logger.error(f"MCP server error: {e}", exc_info=True)
                if not shutdown_event.is_set():
                    logger.info("Restarting MCP server in 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                break
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await cleanup_services()
        logger.info("=== PRODUCTION SERVER STOPPED ===")

def run_server_blocking():
    """Run server in blocking mode for simple deployment"""
    logger.info("Starting MCP server in blocking mode...")
    logger.info("=== MCP SERVER STARTING ===")
    logger.info("Server will handle MCP connections on stdio")
    logger.info("Available tools: chat, search_web, get_weather")
    logger.info("===========================")
    
    try:
        # This blocks until the server is stopped
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        logger.info("=== MCP SERVER STOPPED ===")

def main():
    parser = argparse.ArgumentParser(
        description="Puch.AI MCP Chatbot Server - Production Ready",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --server                    # Run as MCP server
  python main.py --chat "Hello AI"           # Test chat functionality
  python main.py --search "Python news"      # Test search functionality  
  python main.py --weather "London"          # Test weather functionality
  python main.py --config                    # Show current configuration

Environment Variables (can be set in .env file):
  OPENWEATHER_API_KEY    - Your OpenWeatherMap API key (required)
  GEMINI_API_KEY         - Your Google Gemini API key (required)
  GEMINI_MODEL           - Gemini model to use (default: gemini-2.0-flash-exp)
  LOG_LEVEL              - Logging level (default: INFO)
  LOG_FILE               - Log file name (default: puch_chatbot.log)
  SEARCH_TIMEOUT         - Search timeout in seconds (default: 10)
        """
    )
    parser.add_argument("--server", action="store_true", help="Run as MCP server (blocking mode)")
    parser.add_argument("--server-async", action="store_true", help="Run as MCP server (async mode with monitoring)")
    parser.add_argument("--server-persistent", action="store_true", help="Run as persistent MCP server (production mode)")
    parser.add_argument("--chat", type=str, help="Test chat with a message")
    parser.add_argument("--search", type=str, help="Test search with a query")
    parser.add_argument("--weather", type=str, help="Test weather for a city")
    parser.add_argument("--config", action="store_true", help="Show current configuration")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       help="Override log level")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging with config or override
        log_level = args.log_level or config.log_level
        setup_logging(log_level, config.log_file)
        
        logger.info("=== Puch.AI MCP Chatbot Server Starting ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {Path.cwd()}")
        
        if args.config:
            print("\n=== Current Configuration ===")
            print(f"OpenWeather API Key: {config.openweather_api_key[:8]}...")
            print(f"Gemini API Key: {config.gemini_api_key[:8]}...")
            print(f"Gemini Model: {config.gemini_model}")
            print(f"Log Level: {config.log_level}")
            print(f"Log File: {config.log_file}")
            print(f"Search Timeout: {config.search_timeout}s")
            print(f"Search Max Results: {config.search_max_results}")
            return 0
        
        logger.info("Configuration loaded successfully")
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nSolution:")
        print("1. Create a .env file in the project root with:")
        print("   OPENWEATHER_API_KEY=your_openweather_key")
        print("   GEMINI_API_KEY=your_gemini_key")
        print("2. Or set these as environment variables")
        print("\nGet API keys:")
        print("   OpenWeather: https://openweathermap.org/api")
        print("   Gemini: https://makersuite.google.com/app/apikey")
        return 1
    except Exception as e:
        print(f"Unexpected error during configuration: {e}")
        return 1
    
    # Initialize services
    global chat_service, search_service
    try:
        logger.info("Initializing services...")
        chat_service = ChatService(config.gemini_api_key, config.gemini_model)
        search_service = SearchService(config.search_user_agent, config.search_timeout)
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}", exc_info=True)
        print(f"Failed to initialize services: {e}")
        return 1
    
    # Handle different modes
    try:
        if args.server:
            # Blocking MCP server mode (simplest for deployment)
            run_server_blocking()
        elif args.server_async:
            # Async MCP server with monitoring
            asyncio.run(run_server())
        elif args.server_persistent:
            # Persistent production server
            asyncio.run(run_persistent_server())
        elif args.chat:
            asyncio.run(test_chat(args.chat))
        elif args.search:
            asyncio.run(test_search(args.search))
        elif args.weather:
            asyncio.run(test_weather(args.weather))
        else:
            parser.print_help()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}")
        return 1
    finally:
        logger.info("=== Puch.AI MCP Chatbot Server Stopped ===")

if __name__ == "__main__":
    sys.exit(main())
