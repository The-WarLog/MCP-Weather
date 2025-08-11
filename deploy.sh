#!/bin/bash

# Puch.AI MCP Chatbot Server - Production Deployment Script

set -e  # Exit on any error

echo "🚀 Puch.AI MCP Chatbot Server - Production Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Creating .env from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your API keys before continuing"
    print_status "Required variables:"
    echo "  - OPENWEATHER_API_KEY"
    echo "  - GEMINI_API_KEY"
    exit 1
fi

# Validate required environment variables
print_status "Validating configuration..."
source .env

if [ -z "$OPENWEATHER_API_KEY" ] || [ "$OPENWEATHER_API_KEY" = "your_openweather_api_key_here" ]; then
    print_error "OPENWEATHER_API_KEY not set in .env file"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    print_error "GEMINI_API_KEY not set in .env file"
    exit 1
fi

print_success "Configuration validated"

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs data
print_success "Directories created"

# Check deployment method
DEPLOY_METHOD=${1:-"docker"}

case $DEPLOY_METHOD in
    "docker")
        print_status "Deploying with Docker Compose..."
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed. Please install Docker first."
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            print_error "Docker Compose is not installed. Please install Docker Compose first."
            exit 1
        fi
        
        # Build and start the container
        print_status "Building Docker image..."
        docker-compose build
        
        print_status "Starting MCP server container..."
        docker-compose up -d
        
        print_success "MCP server deployed successfully!"
        print_status "Container status:"
        docker-compose ps
        
        print_status "To view logs: docker-compose logs -f"
        print_status "To stop server: docker-compose down"
        ;;
        
    "native")
        print_status "Deploying natively..."
        
        # Check if Python is installed
        if ! command -v python3 &> /dev/null; then
            print_error "Python 3 is not installed. Please install Python 3.13+ first."
            exit 1
        fi
        
        # Install dependencies
        print_status "Installing Python dependencies..."
        pip3 install python-dotenv httpx beautifulsoup4 lxml google-generativeai "mcp[cli]"
        
        # Test configuration
        print_status "Testing configuration..."
        python3 main.py --config
        
        # Create systemd service (Linux only)
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            print_status "Creating systemd service..."
            
            cat > puch-mcp-server.service << EOF
[Unit]
Description=Puch.AI MCP Chatbot Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=/usr/bin:/usr/local/bin
EnvironmentFile=$(pwd)/.env
ExecStart=/usr/bin/python3 $(pwd)/main.py --server-persistent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
            
            print_status "Installing systemd service..."
            sudo mv puch-mcp-server.service /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable puch-mcp-server
            sudo systemctl start puch-mcp-server
            
            print_success "MCP server deployed as systemd service!"
            print_status "Service status:"
            sudo systemctl status puch-mcp-server --no-pager
            
            print_status "To view logs: sudo journalctl -u puch-mcp-server -f"
            print_status "To stop service: sudo systemctl stop puch-mcp-server"
        else
            print_status "Starting MCP server directly..."
            python3 main.py --server-persistent
        fi
        ;;
        
    "test")
        print_status "Running in test mode..."
        
        # Test all features
        print_status "Testing chat functionality..."
        python3 main.py --chat "Hello, this is a deployment test"
        
        print_status "Testing weather functionality..."
        python3 main.py --weather "London"
        
        print_status "Testing search functionality..."
        python3 main.py --search "MCP protocol"
        
        print_success "All tests completed successfully!"
        ;;
        
    *)
        print_error "Unknown deployment method: $DEPLOY_METHOD"
        echo "Usage: $0 [docker|native|test]"
        echo ""
        echo "  docker  - Deploy using Docker Compose (recommended)"
        echo "  native  - Deploy natively on the system"
        echo "  test    - Run tests to verify functionality"
        exit 1
        ;;
esac

print_success "🎉 Deployment completed successfully!"
echo ""
echo "📊 Server Information:"
echo "  - Available MCP tools: chat, search_web, get_weather"
echo "  - Logs location: ./logs/puch_chatbot.log"
echo "  - Configuration: .env file"
echo ""
echo "🔗 API Keys Used:"
echo "  - OpenWeather: ${OPENWEATHER_API_KEY:0:8}..."
echo "  - Gemini: ${GEMINI_API_KEY:0:8}..."
echo ""
echo "📚 Documentation:"
echo "  - README.md - Setup and usage guide"
echo "  - DEPLOYMENT.md - Detailed deployment information"
echo ""
print_success "Your Puch.AI MCP Chatbot Server is now running! 🚀"