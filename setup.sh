#!/bin/bash

################################################################################
# IRA Workflow Builder - Complete Setup Script
################################################################################
# This script sets up the complete development environment including:
# - Python environment with all AI/backend dependencies
# - Node.js environment with frontend dependencies
# - Required system dependencies
# - Environment configuration
################################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print header
print_header() {
    echo ""
    echo "================================================================================"
    echo "                    IRA WORKFLOW BUILDER - SETUP SCRIPT"
    echo "================================================================================"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Check Python version
check_python_version() {
    log_info "Checking Python version..."

    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ] && [ "$PYTHON_MINOR" -le 12 ]; then
            log_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
            return 0
        else
            log_warning "Python $PYTHON_VERSION found, but 3.11-3.12 is recommended"
            PYTHON_CMD="python3"
            return 0
        fi
    else
        log_error "Python 3 not found. Please install Python 3.11 or 3.12"
        return 1
    fi
}

# Check Node.js version
check_node_version() {
    log_info "Checking Node.js version..."

    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)

        if [ "$NODE_MAJOR" -ge 18 ]; then
            log_success "Node.js $NODE_VERSION found"
            return 0
        else
            log_warning "Node.js $NODE_VERSION found, but v18 LTS or higher is recommended"
            return 0
        fi
    else
        log_error "Node.js not found. Please install Node.js 18 LTS"
        return 1
    fi
}

# Install system dependencies
install_system_dependencies() {
    log_info "Installing system dependencies..."

    OS=$(detect_os)

    if [ "$OS" == "macos" ]; then
        if ! command_exists brew; then
            log_error "Homebrew not found. Please install from https://brew.sh"
            exit 1
        fi

        log_info "Installing macOS dependencies via Homebrew..."
        brew update

        # Install Python if not present
        if ! command_exists python3; then
            brew install python@3.11
        fi

        # Install Node.js if not present
        if ! command_exists node; then
            brew install node@18
        fi

        log_success "macOS dependencies installed"

    elif [ "$OS" == "linux" ]; then
        log_info "Installing Linux dependencies..."

        # Detect Linux distro
        if command_exists apt-get; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y python3.11 python3.11-venv python3-pip nodejs npm build-essential
        elif command_exists yum; then
            # RHEL/CentOS
            sudo yum install -y python3.11 python3-pip nodejs npm gcc gcc-c++ make
        else
            log_warning "Unknown Linux distribution. Please install Python 3.11 and Node.js 18 manually"
        fi

        log_success "Linux dependencies installed"
    else
        log_error "Unsupported operating system"
        exit 1
    fi
}

# Create Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."

    if [ -d "venv" ]; then
        log_warning "Virtual environment already exists. Skipping creation..."
    else
        $PYTHON_CMD -m venv venv
        log_success "Virtual environment created"
    fi

    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel

    log_success "Python environment ready"
}

# Install Python dependencies
install_python_dependencies() {
    log_info "Installing Python dependencies..."

    # Ensure we're in virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        log_info "Activating virtual environment..."
        source venv/bin/activate
    fi

    # Check if setup.py exists
    if [ -f "setup.py" ]; then
        log_info "Installing from setup.py..."
        pip install -e .
    else
        log_error "setup.py not found!"
        exit 1
    fi

    # Install additional development dependencies if requirements-dev.txt exists
    if [ -f "requirements-dev.txt" ]; then
        log_info "Installing development dependencies..."
        pip install -r requirements-dev.txt
    fi

    log_success "Python dependencies installed"
}

# Install frontend dependencies
install_frontend_dependencies() {
    log_info "Installing frontend dependencies..."

    if [ ! -d "frontend" ]; then
        log_error "Frontend directory not found!"
        exit 1
    fi

    cd frontend

    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        log_error "package.json not found in frontend directory!"
        cd ..
        exit 1
    fi

    # Install Node.js dependencies
    log_info "Running npm install..."
    npm install

    cd ..

    log_success "Frontend dependencies installed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    mkdir -p storage/workflows
    mkdir -p storage/generated_code
    mkdir -p data/outputs
    mkdir -p logs

    log_success "Directories created"
}

# Setup environment variables
setup_environment() {
    log_info "Setting up environment variables..."

    if [ -f ".env" ]; then
        log_warning ".env file already exists. Skipping..."
        return 0
    fi

    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success ".env file created from .env.example"
        log_warning "Please edit .env file and add your API keys!"
    else
        log_warning ".env.example not found. Creating basic .env file..."

        cat > .env << 'EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile

# LLM Provider Configuration
PLANNER_PROVIDER=groq
CODER_PROVIDER=groq

# Production API Tokens
STAGING_API_TOKEN=your_staging_token_here
PRODUCTION_API_TOKEN=your_production_token_here

# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# File Upload Configuration
MAX_FILE_SIZE=104857600
ALLOWED_FILE_TYPES=[".csv",".xlsx",".xls"]

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF

        log_success ".env file created"
        log_warning "⚠️  IMPORTANT: Please edit .env file and add your actual API keys!"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    # Check Python packages
    log_info "Checking Python packages..."
    source venv/bin/activate

    REQUIRED_PACKAGES=("fastapi" "uvicorn" "pandas" "agent-framework" "pydantic")
    MISSING_PACKAGES=()

    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! pip show "$package" >/dev/null 2>&1; then
            MISSING_PACKAGES+=("$package")
        fi
    done

    if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
        log_success "All required Python packages installed"
    else
        log_error "Missing Python packages: ${MISSING_PACKAGES[*]}"
        return 1
    fi

    # Check Node modules
    log_info "Checking frontend dependencies..."
    if [ -d "frontend/node_modules" ]; then
        log_success "Frontend dependencies installed"
    else
        log_error "Frontend node_modules not found"
        return 1
    fi

    log_success "Installation verification complete!"
}

# Print next steps
print_next_steps() {
    echo ""
    echo "================================================================================"
    echo "                          SETUP COMPLETE!"
    echo "================================================================================"
    echo ""
    log_success "IRA Workflow Builder has been successfully set up!"
    echo ""
    echo "Next Steps:"
    echo ""
    echo "1. Configure API Keys:"
    echo "   Edit .env file and add your OpenAI/Groq API keys:"
    echo "   ${YELLOW}nano .env${NC}"
    echo ""
    echo "2. Start the Backend Server:"
    echo "   ${YELLOW}./start_backend.sh${NC}"
    echo "   Backend will run on: http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo ""
    echo "3. Start the Frontend (in a new terminal):"
    echo "   ${YELLOW}cd frontend && npm run dev${NC}"
    echo "   Frontend will run on: http://localhost:3000"
    echo ""
    echo "4. Access the Application:"
    echo "   Open your browser and navigate to: ${GREEN}http://localhost:3000${NC}"
    echo ""
    echo "================================================================================"
    echo ""
    echo "Documentation:"
    echo "  - README.md - General overview"
    echo "  - HOW_TO_RUN.md - Running instructions"
    echo "  - API Docs - http://localhost:8000/docs (after starting backend)"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check logs in: ./logs/"
    echo "  - Backend logs: ./start_backend.sh output"
    echo "  - Frontend logs: npm run dev output"
    echo ""
    echo "================================================================================"
    echo ""
}

# Main setup function
main() {
    print_header

    log_info "Starting IRA Workflow Builder setup..."
    log_info "This will install all dependencies and configure the environment"
    echo ""

    # Change to script directory
    cd "$(dirname "$0")"

    # Check prerequisites
    log_info "Checking prerequisites..."
    check_python_version || install_system_dependencies
    check_node_version || install_system_dependencies

    # Setup Python environment
    setup_python_env

    # Install dependencies
    install_python_dependencies
    install_frontend_dependencies

    # Create directories
    create_directories

    # Setup environment
    setup_environment

    # Verify installation
    verify_installation

    # Print next steps
    print_next_steps

    log_success "Setup completed successfully!"
}

# Run main function
main "$@"
