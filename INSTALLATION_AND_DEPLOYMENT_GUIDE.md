# PRADYSAGI Complete System - Deployment & Installation Guide

## 🚀 Quick Start (One Command)

### For Linux/macOS

```bash
git clone https://github.com/prady/pradysagican.git
cd pradysagican
./install.sh
```

### For Windows

```bash
git clone https://github.com/prady/pradysagican.git
cd pradysagican
install.bat
```

---

## 📋 Prerequisites

- **Python 3.11+** (check: `python --version`)
- **Git** (check: `git --version`)
- **pip** (included with Python)
- **Optional:** Ollama (for local models) - https://ollama.com/download

---

## 🔧 Manual Installation

### 1. Clone Repository

```bash
git clone https://github.com/prady/pradysagican.git
cd pradysagican
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

This installs PRADYSAGI with all core dependencies.

### 4. Configure System

**Interactive Setup:**
```bash
pradysagi configure
```

**Or Manual Setup:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 5. Verify Installation

```bash
pradysagi status
```

Should show:
- ✅ Component health
- ✅ Available tools
- ✅ System statistics

---

## 💻 Usage

### Interactive Chat

```bash
pradysagi chat
```

```
╔════════════════════════════════════════════════════╗
║                    Chat Mode                       ║
║ Type messages and press Enter. Type 'quit' to exit ║
╚════════════════════════════════════════════════════╝

You: What is machine learning?
PRADYSAGI: Machine learning is...
```

### Autonomous Agent

```bash
pradysagi agent "Analyze this data and write a report"
```

### API Server

```bash
pradysagi server
```

Then access:
- **REST API**: http://localhost:8000/api/v2/chat
- **WebSocket**: ws://localhost:8000/ws/v2/chat
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Check Status

```bash
pradysagi status
```

### Configure System

```bash
pradysagi configure
```

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t pradysagi:latest .
```

### Run Container

```bash
docker run -p 8000:3000 pradysagi:latest
```

### Docker Compose (Full Stack)

```bash
docker-compose up
```

This starts:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Database**: PostgreSQL
- **Cache**: Redis

---

## ☁️ Cloud Deployment

### AWS Lambda

```bash
# Deploy to AWS Lambda
sam build
sam deploy
```

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy pradysagi \
  --source . \
  --platform managed \
  --port 8000
```

### Azure Container Apps

```bash
# Deploy to Azure
az containerapp up \
  --name pradysagi \
  --resource-group my-rg \
  --location eastus
```

### Vercel (Frontend)

```bash
# Deploy React frontend
vercel deploy
```

---

## 📦 Configuration

### Environment Variables

Create `.env` file:

```bash
# Mode: local_only, cloud_only, hybrid
MODE=hybrid

# Features
ENABLE_RAG=true
ENABLE_TOOLS=true

# API Keys (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost/pradysagi

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Feature Toggles

```bash
# Disable RAG
pradysagi chat --enable-rag=False

# Disable tools
pradysagi chat --enable-tools=False

# Custom system prompt
pradysagi chat --system-prompt "You are an expert..."
```

---

## 🛠️ Local Model Setup (Ollama)

### Install Ollama

https://ollama.com/download

### Pull Models

```bash
# Claude-like model
ollama pull neural-chat

# Fast model
ollama pull mistral

# Powerful model
ollama pull neural-chat:34b
```

### Start Ollama

```bash
ollama serve
```

Then PRADYSAGI will automatically use local models when available!

---

## 📊 System Requirements

| Component | Requirement | Optional |
|-----------|-------------|----------|
| Python | 3.11+ | Required |
| RAM | 4GB | 8GB+ recommended |
| Disk | 2GB | 10GB+ for models |
| Network | Internet | For cloud models |
| GPU | - | NVIDIA for acceleration |

### Minimal Setup (Local Only)
- Python 3.11+
- 4GB RAM
- 2GB disk

### Recommended Setup (Hybrid)
- Python 3.11+
- 8GB RAM
- 10GB disk
- Internet connection
- Optional: GPU for Ollama

### Production Setup
- Python 3.11+
- 16GB+ RAM
- 50GB+ disk
- High-speed internet
- GPU recommended
- PostgreSQL database
- Redis cache
- Load balancer
- Monitoring (Prometheus)

---

## 🚀 Production Deployment Checklist

- [ ] Python 3.11+ installed and verified
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Environment variables configured (`.env`)
- [ ] API keys added for cloud models (optional)
- [ ] Local models downloaded (optional, for offline mode)
- [ ] Database migrated (if using PostgreSQL)
- [ ] HTTPS certificate configured
- [ ] Firewall rules configured
- [ ] Monitoring/logging setup
- [ ] Backup strategy in place
- [ ] Rate limiting configured
- [ ] Authentication enabled
- [ ] CORS settings secured
- [ ] Cache warming strategy planned

---

## 🔍 Troubleshooting

### Installation Issues

**Problem**: `pip install -e .` fails

**Solution**:
```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```

**Problem**: Virtual environment not activating

**Solution** (Linux/macOS):
```bash
source venv/bin/activate
```

**Solution** (Windows):
```bash
venv\Scripts\activate.bat
```

### Runtime Issues

**Problem**: "No module named pradysagican"

**Solution**:
```bash
pip install -e .
```

**Problem**: Ollama connection error

**Solution**:
1. Install Ollama: https://ollama.com/download
2. Start Ollama: `ollama serve`
3. Test: `curl http://localhost:11434/api/health`

**Problem**: API key errors

**Solution**:
1. Check `.env` file exists
2. Verify API keys are valid
3. Use `pradysagi configure` to setup

**Problem**: Port 8000 already in use

**Solution**:
```bash
pradysagi server --port 9000
```

---

## 📚 Next Steps After Installation

### 1. Try the Chat Interface

```bash
pradysagi chat
```

### 2. Start the API Server

```bash
pradysagi server
```

### 3. Test REST API

```bash
curl -X POST http://localhost:8000/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is AI?"}'
```

### 4. Test WebSocket

```bash
# Use a WebSocket client or curl
wscat -c ws://localhost:8000/ws/v2/chat
```

### 5. Add RAG Documents

```bash
curl -X POST http://localhost:8000/api/v2/rag/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"content": "Machine learning is...", "source": "ML101"},
      {"content": "Deep learning uses neural networks", "source": "DL101"}
    ]
  }'
```

### 6. Check Status

```bash
pradysagi status
```

### 7. Run Agent

```bash
pradysagi agent "Analyze this complex problem"
```

---

## 🔄 Updates & Upgrades

### Update PRADYSAGI

```bash
git pull origin main
pip install -e --upgrade .
```

### Check Version

```bash
pradysagi --version
```

### Changelog

See: https://github.com/prady/pradysagican/blob/main/CHANGELOG.md

---

## 🤝 Contributing

### Development Setup

```bash
# Clone
git clone https://github.com/prady/pradysagican.git
cd pradysagican

# Setup venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy pradysagican
```

### Create PR

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `pytest`
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature/my-feature`
6. Open PR on GitHub

---

## 📞 Support

- **Issues**: https://github.com/prady/pradysagican/issues
- **Discussions**: https://github.com/prady/pradysagican/discussions
- **Email**: f20240323@dubai.bits-pilani.ac.in

---

## 📄 License

See LICENSE file for details.

---

## 🎯 System Architecture

```
┌─────────────────────────────────────────────────┐
│         PRADYSAGI Complete System               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐    ┌──────────────┐          │
│  │  Web UI      │    │  CLI Tool    │          │
│  │  (React)     │    │  (Click)     │          │
│  └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │
│         └───────────┬───────┘                   │
│                     │                           │
│         ┌───────────▼────────────┐              │
│         │   FastAPI Server       │              │
│         │   (REST + WebSocket)   │              │
│         └───────────┬────────────┘              │
│                     │                           │
│    ┌────────────────┼────────────────┐          │
│    │                │                │          │
│ ┌──▼──┐      ┌──────▼───┐    ┌──────▼───┐     │
│ │ RAG │      │   MCP    │    │  Model   │     │
│ │     │      │  Manager │    │  Router  │     │
│ └─────┘      └──────────┘    └──────────┘     │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  34-Phase PRADYSAGI Core Intelligence   │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘

Local Models: Claude, DeepSeek (via Ollama)
Cloud Models: GPT-4, Claude (via API)
Tools: 14+ MCP tools built-in
RAG: Vector + keyword hybrid search
Database: PostgreSQL + Redis (optional)
```

---

## ✨ What You Get

**Core System (A):**
- ✅ ModelRouter: Multi-model LLM routing
- ✅ MCPManager: 14+ integrated tools
- ✅ RAGEngine: Context-aware retrieval
- ✅ Integration: Unified interface

**API & Real-Time (B):**
- ✅ FastAPI: REST + WebSocket
- ✅ Streaming: Real-time responses
- ✅ Tool execution: MCP support
- ✅ Health monitoring: Status checks

**Interfaces (C & D):**
- ✅ Web UI: React frontend
- ✅ CLI: Click-based terminal
- ✅ REST API: Full HTTP interface
- ✅ WebSocket: Real-time streaming

**Infrastructure:**
- ✅ Docker: Containerization
- ✅ Docker Compose: Full stack
- ✅ AWS/GCP/Azure: Cloud ready
- ✅ Installation scripts: One-command setup

---

## 🎉 Ready to Deploy!

```bash
# One-command quick start
git clone https://github.com/prady/pradysagican.git
cd pradysagican
./install.sh  # or install.bat on Windows

# Then try:
pradysagi chat        # Interactive chat
pradysagi server      # Start API server
pradysagi status      # Check system
```

**Enjoy your superintelligent agent system!** 🚀
