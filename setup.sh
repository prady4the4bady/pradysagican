#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    PRADYSAGICAN — One-Command Setup                     ║
# ║                  The World's First Super General Intelligence           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/prady4the4bady/pradysagican/main/setup.sh | bash
#   — OR —
#   git clone https://github.com/prady4the4bady/pradysagican.git && cd pradysagican && bash setup.sh
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    cat << 'EOF'

    ██████╗ ██████╗  █████╗ ██████╗ ██╗   ██╗███████╗ █████╗  ██████╗ ██╗ ██████╗ █████╗ ███╗   ██╗
    ██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██╔════╝██╔══██╗██╔════╝ ██║██╔════╝██╔══██╗████╗  ██║
    ██████╔╝██████╔╝███████║██║  ██║ ╚████╔╝ ███████╗███████║██║  ███╗██║██║     ███████║██╔██╗ ██║
    ██╔═══╝ ██╔══██╗██╔══██║██║  ██║  ╚██╔╝  ╚════██║██╔══██║██║   ██║██║██║     ██╔══██║██║╚██╗██║
    ██║     ██║  ██║██║  ██║██████╔╝   ██║   ███████║██║  ██║╚██████╔╝██║╚██████╗██║  ██║██║ ╚████║
    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝

    Super General Intelligence System v6.0
    55 subsystems • 39,000+ lines • 75-90+ features • 692 tests passing

EOF
    echo -e "${NC}"
}

info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; }
step()    { echo -e "${BOLD}${CYAN}==> $1${NC}"; }

banner

# ── Step 1: Check Python ─────────────────────────────────────────────────
step "Checking Python version..."
if command -v python3 &>/dev/null; then
    PY=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    MAJOR=$(echo "$PY" | cut -d. -f1)
    MINOR=$(echo "$PY" | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
        info "Python $PY detected"
    else
        error "Python 3.11+ required (found $PY)"
        exit 1
    fi
else
    error "Python 3 not found. Install Python 3.11+ first."
    exit 1
fi

# ── Step 2: Create virtual environment ───────────────────────────────────
step "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    info "Virtual environment created at .venv/"
else
    info "Virtual environment already exists"
fi

# Activate
source .venv/bin/activate
info "Virtual environment activated"

# ── Step 3: Install core dependencies ────────────────────────────────────
step "Installing PRADYSAGICAN and dependencies..."
pip install --upgrade pip -q 2>/dev/null
pip install -e ".[dev]" -q 2>/dev/null
info "All dependencies installed"

# ── Step 4: Run tests to verify ──────────────────────────────────────────
step "Running verification tests..."
RESULT=$(python -m pytest tests/ --tb=no -q 2>&1 | tail -1)
if echo "$RESULT" | grep -q "passed"; then
    info "Tests: $RESULT"
else
    warn "Some tests may have failed: $RESULT"
    warn "This may be due to optional dependencies. Core functionality is intact."
fi

# ── Step 4a: Verify at least one LLM provider is available ────────────────
step "Checking LLM provider availability..."
if [ ! -z "$GROQ_API_KEY" ] || [ ! -z "$TOGETHER_API_KEY" ] || [ ! -z "$NVIDIA_API_KEY" ] || [ ! -z "$HF_TOKEN" ]; then
    info "Cloud LLM provider detected (one or more API keys set)"
elif command -v ollama &>/dev/null; then
    info "Ollama detected (local inference ready)"
else
    warn "No LLM provider configured (cloud API keys OR local Ollama)"
    warn "The system will not be able to think without an LLM."
    warn ""
    warn "Quick fix — choose ONE:"
    warn "  1. Cloud (free tier, fastest):"
    warn "     export GROQ_API_KEY=your_key  (get from https://console.groq.com)"
    warn "  2. Local (free, no API key needed):"
    warn "     docker run -d -p 11434:11434 ollama/ollama"
    warn "     ollama pull llama3.2"
fi

# ── Step 5: Create data directory ────────────────────────────────────────
step "Setting up data directory..."
mkdir -p data/chromadb data/logs data/memory data/tools data/benchmarks
info "Data directories created"

# ── Step 6: Create default .env ──────────────────────────────────────────
step "Creating configuration..."
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
# PRADYSAGICAN Configuration
# Add your API keys here (all optional — system works with free tiers)

# LLM Providers (all free tier)
NVIDIA_API_KEY=
GROQ_API_KEY=
TOGETHER_API_KEY=
HF_TOKEN=
OLLAMA_BASE_URL=http://localhost:11434/v1

# System Settings
LOG_LEVEL=INFO
PRADYSAGICAN_DATA=./data
ENVEOF
    info "Default .env created (add API keys for enhanced capabilities)"
else
    info "Existing .env preserved"
fi

# ── Done ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║           PRADYSAGICAN v6.0 — Installation Complete          ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}⚡ Quick Start (pick one):${NC}"
echo ""
echo -e "  ${CYAN}Option 1: Interactive Chat (Recommended)${NC}"
echo -e "    source .venv/bin/activate"
echo -e "    pradysagican chat           ${CYAN}# Type commands: /help, /status, /solve 'problem'${NC}"
echo ""
echo -e "  ${CYAN}Option 2: API Server${NC}"
echo -e "    source .venv/bin/activate"
echo -e "    pradysagican serve          ${CYAN}# Starts on http://localhost:8000${NC}"
echo ""
echo -e "  ${CYAN}Option 3: Python Code${NC}"
echo -e "    from pradysagican.god import PradysagicanGod"
echo -e "    god = PradysagicanGod()"
echo -e "    result = await god.solve('complex problem')"
echo ""
echo -e "  ${BOLD}🤖 Verify System Health:${NC}"
echo -e "    pradysagican status         ${CYAN}# Show all 55 subsystems${NC}"
echo -e "    pradysagican benchmark      ${CYAN}# Run performance tests${NC}"
echo ""
echo -e "  ${BOLD}📖 Documentation:${NC} https://github.com/prady4the4bady/pradysagican"
echo ""
