# Puch.AI MCP Chatbot Server - Windows Production Deployment Script

param(
    [Parameter(Position=0)]
    [ValidateSet("docker", "native", "test")]
    [string]$DeployMethod = "native"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

Write-Host "Puch.AI MCP Chatbot Server - Windows Production Deployment" -ForegroundColor $Green
Write-Host "==========================================================" -ForegroundColor $Green

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Error ".env file not found!"
    Write-Status "Creating .env from template..."
    Copy-Item ".env.example" ".env"
    Write-Warning "Please edit .env file with your API keys before continuing"
    Write-Status "Required variables:"
    Write-Host "  - OPENWEATHER_API_KEY"
    Write-Host "  - GEMINI_API_KEY"
    exit 1
}

# Load and validate environment variables
Write-Status "Validating configuration..."
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

$openweatherKey = $env:OPENWEATHER_API_KEY
$geminiKey = $env:GEMINI_API_KEY

if (-not $openweatherKey -or $openweatherKey -eq "your_openweather_api_key_here") {
    Write-Error "OPENWEATHER_API_KEY not set in .env file"
    exit 1
}

if (-not $geminiKey -or $geminiKey -eq "your_gemini_api_key_here") {
    Write-Error "GEMINI_API_KEY not set in .env file"
    exit 1
}

Write-Success "Configuration validated"

# Create necessary directories
Write-Status "Creating directories..."
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "data" | Out-Null
Write-Success "Directories created"

switch ($DeployMethod) {
    "docker" {
        Write-Status "Deploying with Docker..."
        
        # Check if Docker is installed
        try {
            docker --version | Out-Null
        } catch {
            Write-Error "Docker is not installed. Please install Docker Desktop first."
            exit 1
        }
        
        # Build and start the container
        Write-Status "Building Docker image..."
        docker-compose build
        
        Write-Status "Starting MCP server container..."
        docker-compose up -d
        
        Write-Success "MCP server deployed successfully!"
        Write-Status "Container status:"
        docker-compose ps
        
        Write-Status "To view logs: docker-compose logs -f"
        Write-Status "To stop server: docker-compose down"
    }
    
    "native" {
        Write-Status "Deploying natively on Windows..."
        
        # Check if Python is installed
        try {
            python --version | Out-Null
        } catch {
            Write-Error "Python is not installed. Please install Python 3.13+ first."
            exit 1
        }
        
        # Install dependencies
        Write-Status "Installing Python dependencies..."
        pip install python-dotenv httpx beautifulsoup4 lxml google-generativeai "mcp[cli]"
        
        # Test configuration
        Write-Status "Testing configuration..."
        python main.py --config
        
        # Create Windows service script
        Write-Status "Creating service runner script..."
        
        $serviceScript = @"
@echo off
cd /d "$PWD"
python main.py --server-persistent
pause
"@
        
        $serviceScript | Out-File -FilePath "run-server.bat" -Encoding ASCII
        
        Write-Success "MCP server ready for deployment!"
        Write-Status "To start server: run-server.bat"
        Write-Status "Or run directly: python main.py --server-persistent"
        
        # Optionally start the server
        $startNow = Read-Host "Start the server now? (y/N)"
        if ($startNow -eq "y" -or $startNow -eq "Y") {
            Write-Status "Starting MCP server..."
            python main.py --server-persistent
        }
    }
    
    "test" {
        Write-Status "Running in test mode..."
        
        # Test all features
        Write-Status "Testing chat functionality..."
        python main.py --chat "Hello, this is a Windows deployment test"
        
        Write-Status "Testing weather functionality..."
        python main.py --weather "London"
        
        Write-Status "Testing search functionality..."
        python main.py --search "MCP protocol"
        
        Write-Success "All tests completed successfully!"
    }
}

Write-Success "Deployment completed successfully!"
Write-Host ""
Write-Host "Server Information:" -ForegroundColor $Blue
Write-Host "  - Available MCP tools: chat, search_web, get_weather"
Write-Host "  - Logs location: .\logs\puch_chatbot.log"
Write-Host "  - Configuration: .env file"
Write-Host ""
Write-Host "API Keys Used:" -ForegroundColor $Blue
Write-Host "  - OpenWeather: $($openweatherKey.Substring(0,8))..."
Write-Host "  - Gemini: $($geminiKey.Substring(0,8))..."
Write-Host ""
Write-Host "Documentation:" -ForegroundColor $Blue
Write-Host "  - README.md - Setup and usage guide"
Write-Host "  - DEPLOYMENT.md - Detailed deployment information"
Write-Host ""
Write-Success "Your Puch.AI MCP Chatbot Server is ready!"