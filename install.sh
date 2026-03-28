#!/bin/bash
# PRADYSAGI Installation Script (Linux/macOS)
# Installs complete PRADYSAGI system with all dependencies

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ ${1}${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${YELLOW}→ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

# Check Python version
print_header "PRADYSAGI Installation"

print_step "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python ${PYTHON_VERSION} found"

# Check Python minimum version
REQUIRED_VERSION="3.11"
if [[ $(echo -e "$PYTHON_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) != "$REQUIRED_VERSION" ]]; then
    print_error "Python 3.11+ required (found ${PYTHON_VERSION})"
    exit 1
fi

# Check Git
print_step "Checking Git..."
if ! command -v git &> /dev/null; then
    print_error "Git not found. Please install Git."
    exit 1
fi
print_success "Git found"

# Create virtual environment
print_step "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_step "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_success "pip upgraded"

# Install dependencies
print_step "Installing PRADYSAGI..."
pip install -e . > /dev/null 2>&1
print_success "PRADYSAGI installed"

# Check optional dependencies
print_step "Installing optional dependencies..."
pip install rich click > /dev/null 2>&1
print_success "Optional dependencies installed"

# Verify installation
print_step "Verifying installation..."
if python -c "from pradysagican.core.integration import pradysagi" 2>/dev/null; then
    print_success "Installation verified"
else
    print_error "Installation verification failed"
    exit 1
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    print_step "Creating .env configuration file..."
    cat > .env << 'EOF'
# PRADYSAGI Configuration
MODE=hybrid
ENABLE_RAG=true
ENABLE_TOOLS=true
HOST=0.0.0.0
PORT=8000

# API Keys (optional - fill in if using cloud models)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
EOF
    print_success ".env configuration created"
fi

# Summary
print_header "Installation Complete! ✨"

echo -e "${GREEN}PRADYSAGI is ready to use!${NC}\n"

echo "Next steps:"
echo ""
echo -e "  ${YELLOW}1. Start interactive chat:${NC}"
echo -e "     ${BLUE}pradysagi chat${NC}"
echo ""
echo -e "  ${YELLOW}2. Start API server:${NC}"
echo -e "     ${BLUE}pradysagi server${NC}"
echo ""
echo -e "  ${YELLOW}3. Check system status:${NC}"
echo -e "     ${BLUE}pradysagi status${NC}"
echo ""
echo -e "  ${YELLOW}4. Run configuration wizard:${NC}"
echo -e "     ${BLUE}pradysagi configure${NC}"
echo ""
echo "Documentation: ${BLUE}https://github.com/prady/pradysagican${NC}"
echo ""
print_success "Ready to deploy!"
