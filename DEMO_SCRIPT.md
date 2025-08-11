# 🎬 Puch.AI MCP Chatbot Server - Demo Video Script

## 🎯 **Demo Video Structure (5-7 minutes)**

### **INTRO (30 seconds)**
*"Hi! I'm demonstrating my MCP Chatbot Server for the Puch.ai hackathon. This is a production-ready Model Context Protocol server that provides AI chat, weather data, and web search - all without requiring Google API keys."*

---

## 📋 **STEP-BY-STEP DEMO COMMANDS**

### **STEP 1: Show Project Overview (30 seconds)**

**Command:**
```powershell
dir
```

**Say:** *"Here's our project structure. We have a production-ready MCP server with deployment scripts, Docker support, and comprehensive documentation."*

**Show files:**
- `main.py` - Main server
- `deploy.ps1` - Windows deployment
- `docker-compose.yml` - Container deployment
- `.env` - Secure configuration

---

### **STEP 2: Verify Configuration (30 seconds)**

**Command:**
```powershell
python main.py --config
```

**Say:** *"First, let's verify our server configuration. Notice how we securely load API keys from environment files and mask them in logs for security."*

**Point out:**
- ✅ API keys loaded securely
- ✅ Production logging configured
- ✅ All services ready

---

### **STEP 3: Test AI Chat Tool (60 seconds)**

**Command:**
```powershell
python main.py --chat "Explain what MCP is and why it's revolutionary for AI development"
```

**Say:** *"Let's test our AI chat tool powered by Gemini 2.5 Flash. I'm asking it to explain MCP and why it's revolutionary."*

**Wait for response, then say:** *"As you can see, we get intelligent, detailed responses. The chat service handles async processing and proper error handling."*

---

### **STEP 4: Test Weather Tool (45 seconds)**

**Command:**
```powershell
python main.py --weather "Tokyo"
```

**Say:** *"Now let's test our weather tool using the OpenWeatherMap API. I'm getting current weather for Tokyo."*

**Point out:**
- Real-time weather data
- Temperature, humidity, conditions
- Proper error handling and validation

---

### **STEP 5: Test Search Tool (60 seconds)**

**Command:**
```powershell
python main.py --search "latest AI developments 2025"
```

**Say:** *"Here's our web search tool - and this is special because it works WITHOUT requiring Google API keys. We use respectful web scraping with smart fallbacks."*

**Point out:**
- No API keys required
- Fallback responses when scraping is limited
- Suggests using chat for detailed information

---

### **STEP 6: Start Production Server (45 seconds)**

**Command:**
```powershell
python main.py --server-persistent
```

**Say:** *"Now let's start our production server. This runs continuously and can handle multiple MCP client connections simultaneously."*

**Let it run for 10 seconds showing logs, then Ctrl+C**

**Point out:**
- Production logging
- Health monitoring
- Graceful shutdown handling

---

### **STEP 7: Show MCP Integration in Kiro (90 seconds)**

**Action:** Open Kiro IDE and show MCP panel

**Say:** *"The real power comes from MCP integration. Here in Kiro IDE, our server appears as 'puch-chatbot' with three available tools."*

**Demonstrate in Kiro:**

1. **Use chat tool:**
   ```
   Message: "What's the weather like in London and what activities would be good for that weather?"
   ```

2. **Use get_weather tool:**
   ```
   City: "San Francisco"
   Units: "metric"
   ```

3. **Use search_web tool:**
   ```
   Query: "Puch.ai hackathon MCP protocol"
   Results: 5
   ```

**Say:** *"Notice how these tools can work together - the AI can use weather data to make activity recommendations, combining multiple data sources intelligently."*

---

### **STEP 8: Show Production Features (60 seconds)**

**Command:**
```powershell
# Show logs
type logs\puch_chatbot.log | Select-Object -Last 10

# Show Docker deployment
docker-compose --version
type docker-compose.yml
```

**Say:** *"This isn't just a demo - it's production-ready. We have structured logging with rotation, Docker deployment, health checks, and comprehensive error handling."*

**Point out:**
- Structured logging
- Docker deployment ready
- Health monitoring
- Security best practices

---

### **STEP 9: Show Extensibility (30 seconds)**

**Command:**
```powershell
# Show the code structure
type main.py | Select-Object -First 20
```

**Say:** *"The architecture is designed for extensibility. Adding new MCP tools is as simple as creating a service class and decorating a function with @mcp.tool()."*

---

### **CLOSING (30 seconds)**

**Say:** *"This MCP server demonstrates the power of the Model Context Protocol - creating composable AI tools that work together seamlessly. It's ready for production deployment and showcases how MCP can revolutionize AI assistant development."*

**Final points:**
- ✅ Production-ready with proper DevOps practices
- ✅ No expensive API keys required for search
- ✅ Extensible architecture for future tools
- ✅ Full MCP protocol compliance
- ✅ Easy deployment anywhere

---

## 🎥 **Recording Tips**

### **Before Recording:**
1. **Clear your terminal history:** `Clear-Host`
2. **Close unnecessary applications**
3. **Set terminal to full screen**
4. **Test all commands once to ensure they work**

### **During Recording:**
1. **Speak clearly and at moderate pace**
2. **Wait for commands to complete before speaking**
3. **Point out key features as they appear**
4. **Keep energy high and enthusiastic**

### **Terminal Setup:**
```powershell
# Make terminal look good
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "Green"
Clear-Host

# Set window title
$Host.UI.RawUI.WindowTitle = "Puch.AI MCP Chatbot Server Demo"
```

---

## 🚀 **Quick Test Run Commands**

**Copy and paste these in order for a quick test:**

```powershell
# 1. Show config
python main.py --config

# 2. Test chat
python main.py --chat "What is MCP and why is it important?"

# 3. Test weather  
python main.py --weather "London"

# 4. Test search
python main.py --search "MCP protocol AI"

# 5. Show logs
type logs\puch_chatbot.log | Select-Object -Last 5
```

---

## 🏆 **Key Messages to Emphasize**

1. **"Production-Ready"** - Not just a prototype
2. **"No API Keys for Search"** - Saves money and complexity
3. **"MCP Protocol Compliant"** - Works with any MCP client
4. **"Extensible Architecture"** - Easy to add new tools
5. **"Deploy Anywhere"** - Docker, native, cloud-ready

**Total Demo Time: 5-7 minutes**
**Perfect for hackathon submission! 🎉**