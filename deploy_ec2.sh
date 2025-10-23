#!/bin/bash

# =============================================================================
# AWS EC2 Deployment Script for IRA Workflow Builder
# =============================================================================
# This script sets up and deploys the application on a fresh Ubuntu EC2 instance
#
# Prerequisites:
# - Ubuntu 20.04+ EC2 instance
# - Minimum 4GB RAM, 2 vCPUs recommended
# - Security group allowing ports: 22 (SSH), 3000 (Frontend), 8000 (Backend)
# - SSH key pair for accessing the instance
#
# Usage:
#   Local machine:  ./deploy_ec2.sh <EC2_PUBLIC_IP>
#   On EC2:         ./deploy_ec2.sh setup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

# Check if running on EC2 or local machine
if [ "$1" == "setup" ]; then
    # Running on EC2 - perform setup
    print_header "IRA Workflow Builder - EC2 Setup"

    # 1. Update system
    print_info "Updating system packages..."
    sudo apt-get update -y
    sudo apt-get upgrade -y

    # 2. Install Python 3.11
    print_info "Installing Python 3.11..."
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update -y
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

    # 3. Install Node.js 20.x
    print_info "Installing Node.js 20.x..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs

    # 4. Install additional tools
    print_info "Installing additional tools..."
    sudo apt-get install -y git curl wget build-essential

    # 5. Install PM2 for process management
    print_info "Installing PM2..."
    sudo npm install -g pm2

    # 6. Create application directory
    print_info "Creating application directory..."
    mkdir -p ~/ira_workflow_builder
    cd ~/ira_workflow_builder

    print_success "System setup complete!"
    print_info "Next steps:"
    echo "  1. Upload your application code to ~/ira_workflow_builder"
    echo "  2. Configure your .env file with API keys"
    echo "  3. Run: ./deploy_ec2.sh start"

elif [ "$1" == "start" ]; then
    # Start the application
    print_header "Starting IRA Workflow Builder"

    cd ~/ira_workflow_builder || exit 1

    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_info "Please create .env file from .env.production template"
        exit 1
    fi

    # 1. Setup Python virtual environment
    print_info "Setting up Python virtual environment..."
    python3.11 -m venv venv
    source venv/bin/activate

    # 2. Install Python dependencies
    print_info "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    # 3. Install frontend dependencies
    print_info "Installing frontend dependencies..."
    cd frontend
    npm install

    # 4. Build frontend
    print_info "Building frontend for production..."
    npm run build

    cd ..

    # 5. Start backend with PM2
    print_info "Starting backend API..."
    pm2 start backend/main.py --name "ira-backend" --interpreter python3.11

    # 6. Start frontend with PM2
    print_info "Starting frontend..."
    cd frontend
    pm2 start npm --name "ira-frontend" -- start
    cd ..

    # 7. Save PM2 configuration
    pm2 save
    pm2 startup

    print_success "Application started successfully!"
    print_info "Services running:"
    pm2 list

    # Get public IP
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    print_success "\nApplication is now accessible at:"
    echo "  Frontend: http://${PUBLIC_IP}:3000"
    echo "  Backend:  http://${PUBLIC_IP}:8000"
    echo "  API Docs: http://${PUBLIC_IP}:8000/docs"

elif [ "$1" == "stop" ]; then
    # Stop the application
    print_header "Stopping IRA Workflow Builder"
    pm2 stop ira-backend ira-frontend
    print_success "Application stopped"

elif [ "$1" == "restart" ]; then
    # Restart the application
    print_header "Restarting IRA Workflow Builder"
    pm2 restart ira-backend ira-frontend
    print_success "Application restarted"

elif [ "$1" == "logs" ]; then
    # View logs
    SERVICE=${2:-all}
    if [ "$SERVICE" == "backend" ]; then
        pm2 logs ira-backend
    elif [ "$SERVICE" == "frontend" ]; then
        pm2 logs ira-frontend
    else
        pm2 logs
    fi

elif [ "$1" == "status" ]; then
    # Check status
    print_header "Application Status"
    pm2 list
    pm2 monit

elif [ ! -z "$1" ]; then
    # Deploy from local machine to EC2
    EC2_IP=$1
    SSH_KEY=${2:-~/.ssh/id_rsa}
    SSH_USER=${3:-ubuntu}

    print_header "Deploying to EC2: $EC2_IP"

    if [ ! -f "$SSH_KEY" ]; then
        print_error "SSH key not found: $SSH_KEY"
        exit 1
    fi

    print_info "Uploading application files..."
    rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '.git' --exclude '__pycache__' \
        -e "ssh -i $SSH_KEY" \
        . ${SSH_USER}@${EC2_IP}:~/ira_workflow_builder/

    print_info "Connecting to EC2 and starting setup..."
    ssh -i "$SSH_KEY" ${SSH_USER}@${EC2_IP} "cd ~/ira_workflow_builder && ./deploy_ec2.sh start"

    print_success "Deployment complete!"

else
    # Show usage
    print_header "IRA Workflow Builder - Deployment Script"
    echo "Usage:"
    echo "  On local machine:"
    echo "    ./deploy_ec2.sh <EC2_PUBLIC_IP> [SSH_KEY] [SSH_USER]"
    echo "    Example: ./deploy_ec2.sh 54.123.45.67 ~/.ssh/my-key.pem ubuntu"
    echo ""
    echo "  On EC2 instance:"
    echo "    ./deploy_ec2.sh setup      # Initial system setup"
    echo "    ./deploy_ec2.sh start      # Start the application"
    echo "    ./deploy_ec2.sh stop       # Stop the application"
    echo "    ./deploy_ec2.sh restart    # Restart the application"
    echo "    ./deploy_ec2.sh status     # Check application status"
    echo "    ./deploy_ec2.sh logs [backend|frontend|all]  # View logs"
fi
