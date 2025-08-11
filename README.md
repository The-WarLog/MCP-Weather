# Puch.AI MCP Chatbot Server

A production-ready MCP (Model Context Protocol) server for the Puch.ai hackathon with:
- 🤖 **AI Chat** using Gemini 2.5 Flash
- 🌤️ **Weather Information** via OpenWeatherMap
- 🔍 **Web Search** using Google (no API key required)
- 🔧 **Production Features**: Logging, graceful shutdown, .env support

## Quick Setup

1. **Clone and install:**
   ```bash
   git clone <your-repo>
   cd weather
   pip install python-dotenv httpx beautifulsoup4 lxml google-generativeai "mcp[cli]"
   ```

2. **Configure API keys:**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your API keys
   # OPENWEATHER_API_KEY=your_openweather_key
   # GEMINI_API_KEY=your_gemini_key
   ```

3. **Test the features:**
   ```bash
   # Check configuration
   python main.py --config
   
   # Test chat
   python main.py --chat "Hello, how are you?"
   
   # Test search
   python main.py --search "Python programming"
   
   # Test weather
   python main.py --weather "London"
   ```

4. **Run as MCP server:**
   ```bash
   # Simple blocking mode (recommended for MCP clients)
   python main.py --server
   
   # Production persistent mode (for deployment)
   python main.py --server-persistent
   
   # Async mode with monitoring
   python main.py --server-async
   ```

## MCP Tools Available

### `chat(message, context?)`
Chat with Gemini 2.5 Flash AI
- `message`: Your message to the AI
- `context`: Optional conversation context

### `search_web(query, num_results?)`
Search Google without API keys
- `query`: Search query string
- `num_results`: Number of results (1-10, default: 5)

### `get_weather(city, units?)`
Get current weather information
- `city`: City name
- `units`: "metric" or "imperial" (default: "metric")

## Configuration

Configuration is loaded from `.env` file or environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENWEATHER_API_KEY` | ✅ Yes | - | Your OpenWeatherMap API key |
| `GEMINI_API_KEY` | ✅ Yes | - | Your Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash-exp` | Gemini model to use |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FILE` | No | `puch_chatbot.log` | Log file name |
| `SEARCH_TIMEOUT` | No | `10` | Search timeout in seconds |
| `SEARCH_MAX_RESULTS` | No | `10` | Maximum search results |
| `SEARCH_USER_AGENT` | No | Chrome UA | User agent for web scraping |

### Getting API Keys

- **OpenWeatherMap**: Free tier (1000 calls/day) at https://openweathermap.org/api
- **Google Gemini**: Free tier available at https://makersuite.google.com/app/apikey

## Example Usage

```python
# In an MCP client
result = await mcp_client.call_tool("chat", {
    "message": "What's the weather like in Tokyo?",
    "context": "We're planning a trip"
})

search_results = await mcp_client.call_tool("search_web", {
    "query": "best restaurants Tokyo",
    "num_results": 5
})

weather = await mcp_client.call_tool("get_weather", {
    "city": "Tokyo",
    "units": "metric"
})
```

## Production Features

- ✅ **Environment Configuration**: `.env` file support with validation
- ✅ **Production Logging**: Rotating file logs with structured output
- ✅ **Graceful Shutdown**: Signal handling for clean server shutdown
- ✅ **Error Handling**: Comprehensive error handling and recovery
- ✅ **Security**: API key masking in logs, .gitignore protection
- ✅ **Input Validation**: Sanitization and validation for all inputs
- ✅ **Async Performance**: Non-blocking operations throughout
- ✅ **Respectful Scraping**: Rate limiting and proper headers
- ✅ **CLI Testing**: Development and debugging modes
- ✅ **Extensible Architecture**: Easy to add new MCP tools

## Hackathon Ready

This server is designed for the Puch.ai hackathon Phase 1 requirements:
- Implements MCP protocol correctly
- Provides useful AI-powered tools
- Easy to deploy and test
- Extensible for future features

## Troubleshooting

### Configuration Issues
```bash
# Check your configuration
python main.py --config

# Common issues:
# 1. Missing .env file - copy from .env.example
# 2. Invalid API keys - check the URLs above for getting new keys
# 3. Permissions - ensure .env file is readable
```

### Service Issues
- **Chat errors**: Check Gemini API key and quota limits
- **Weather errors**: Verify OpenWeatherMap API key and city name
- **Search limited**: Google blocks scraping - use chat for information instead

### Logs and Debugging
```bash
# Check logs
tail -f logs/puch_chatbot.log

# Debug mode
python main.py --log-level DEBUG --chat "test"
```

## Development

### Adding New MCP Tools
1. Create service class in `{feature}_service.py`
2. Add to `main.py` initialization
3. Create `@mcp.tool()` decorated function
4. Update configuration and README

### Project Structure
```
weather/
├── main.py              # Main server and CLI
├── models.py            # Data models and validation
├── chat_service.py      # Gemini AI integration
├── search_service.py    # Google search scraping
├── puch.py             # Original weather service
├── .env                # Configuration (not in git)
├── .env.example        # Configuration template
├── logs/               # Log files (auto-created)
└── README.md           # This file
```

## Production Deployment

### Quick Deploy (Recommended)

**Windows:**
```powershell
# Run the deployment script
.\deploy.ps1 native

# Or test first
.\deploy.ps1 test
```

**Linux/Mac:**
```bash
# Make script executable and run
chmod +x deploy.sh
./deploy.sh native

# Or test first
./deploy.sh test
```

### Docker Deployment

```bash
# Using deployment script
./deploy.sh docker

# Or manually
docker-compose up -d
```

### Manual Production Setup

1. **Environment Configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Install Dependencies:**
   ```bash
   pip install python-dotenv httpx beautifulsoup4 lxml google-generativeai "mcp[cli]"
   ```

3. **Run Production Server:**
   ```bash
   # Persistent mode (recommended for deployment)
   python main.py --server-persistent
   
   # Or simple blocking mode
   python main.py --server
   ```

### Server Modes

- `--server` - Simple blocking MCP server (best for MCP clients)
- `--server-persistent` - Production mode with auto-restart and monitoring
- `--server-async` - Async mode with health monitoring and graceful shutdown

### Monitoring & Logs

- **Logs Location:** `logs/puch_chatbot.log`
- **Log Rotation:** 10MB files, 5 backups
- **Health Checks:** Built-in monitoring every 5 minutes
- **Graceful Shutdown:** Ctrl+C or SIGTERM

Happy hacking! 🚀