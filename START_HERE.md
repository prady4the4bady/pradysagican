# 🚀 START HERE - PRADYSAGI Quick Start Guide

**Welcome to PRADYSAGI - The Complete Superintelligent Agent System!**

---

## ⚡ Quick Start (2 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/prady/pradysagican.git
cd pradysagican
```

### 2. Run Installation
**On Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

**On Windows:**
```bash
install.bat
```

### 3. Try It!
```bash
# Interactive chat
pradysagi chat

# Or start the API server
pradysagi server

# Or check system status
pradysagi status
```

---

## 📚 What You Got

✅ **Multi-Model AI System**
- Local models (Claude, DeepSeek via Ollama)
- Cloud models (GPT-4, Claude via APIs)
- Auto-selection and fallback

✅ **14+ Built-in Tools**
- Execute Python/JavaScript/Shell code
- Read/write/search files
- Browser automation
- Web search

✅ **Context Awareness**
- Hybrid RAG (vector + keyword)
- Document management
- Query augmentation

✅ **Multiple Interfaces**
- Interactive CLI
- REST API
- WebSocket streaming
- Web UI (coming soon)

---

## 💻 Commands

### Chat Interface
```bash
pradysagi chat
```
Start interactive conversation with PRADYSAGI.

### Autonomous Agent
```bash
pradysagi agent "Describe your task here"
```
Run autonomous multi-step reasoning and execution.

### API Server
```bash
pradysagi server
```
Start FastAPI server:
- REST API: http://localhost:8000/api/v2/chat
- WebSocket: ws://localhost:8000/ws/v2/chat
- Docs: http://localhost:8000/docs

### System Status
```bash
pradysagi status
```
Check health and statistics of all components.

### Configuration
```bash
pradysagi configure
```
Interactive setup wizard for API keys and features.

### Help
```bash
pradysagi help
```
Show detailed documentation and examples.

---

## 🔧 Configuration

### Option 1: Interactive Setup
```bash
pradysagi configure
```

### Option 2: Manual Setup
Edit `.env` file:
```bash
# Mode: local_only, cloud_only, or hybrid
MODE=hybrid

# Features
ENABLE_RAG=true
ENABLE_TOOLS=true

# API Keys (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 📖 Full Documentation

After quick start, read:

1. **INSTALLATION_AND_DEPLOYMENT_GUIDE.md**
   - Detailed installation steps
   - Cloud deployment options
   - Troubleshooting guide

2. **FINAL_IMPLEMENTATION_REPORT.md**
   - Complete feature list
   - Architecture overview
   - Performance metrics

3. **IMPLEMENTATION_COMPLETE_SUMMARY.md**
   - Quick feature reference
   - Usage examples
   - Next steps

4. **API Documentation**
   - Run `pradysagi server`
   - Visit http://localhost:8000/docs

---

## 🌐 Deploy to Cloud

### Docker (Local)
```bash
docker build -t pradysagi .
docker run -p 8000:8000 pradysagi
```

### AWS
```bash
sam build
sam deploy
```

### Google Cloud
```bash
gcloud run deploy pradysagi --source .
```

### Azure
```bash
az containerapp up --name pradysagi
```

---

## 🎯 Example Usage

### Interactive Chat Example
```bash
$ pradysagi chat

You: What is machine learning?
🤔 Thinking...

PRADYSAGI: Machine learning is a subset of artificial 
intelligence that focuses on systems learning from data...

Show metadata? (y/n): y
ℹ️  Model: gpt-4
ℹ️  Duration: 1253.4ms
ℹ️  Retrieval: hybrid
```

### Agent Example
```bash
$ pradysagi agent "Analyze this CSV file and generate insights"

🚀 Agent executing task...

Agent Response:
The data shows...
[detailed analysis]

Execution Summary:
Duration: 2145.3ms
Model: gpt-4
Tools Used: 2
Confidence: 92%
```

### REST API Example
```bash
# Start server
pradysagi server &

# Send request
curl -X POST http://localhost:8000/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is AI?",
    "enable_rag": true
  }'

# Response
{
  "query": "What is AI?",
  "response": "Artificial Intelligence is...",
  "model_used": "gpt-4",
  "duration_ms": 1234.5,
  "confidence": 0.92
}
```

---

## ❓ FAQ

**Q: Do I need API keys?**
A: No! Local models work without them. API keys are optional for cloud models.

**Q: Can I use it without Ollama?**
A: Yes! It will use cloud models (if configured). Ollama is optional.

**Q: What models are supported?**
A: Claude, DeepSeek (local), GPT-4, Claude (cloud). More can be added.

**Q: How do I deploy to production?**
A: Use Docker (`docker build`), AWS (`sam deploy`), GCP (`gcloud run deploy`), or Azure (`az containerapp up`).

**Q: Can I integrate with my own tools?**
A: Yes! The MCP Manager is extensible for custom tools.

**Q: Is it production-ready?**
A: Yes! Type-safe, tested, documented, and deployable.

---

## 🆘 Troubleshooting

**Problem:** `Python not found`
- **Solution:** Install Python 3.11+ from https://python.org

**Problem:** `Ollama connection error`
- **Solution:** Install Ollama from https://ollama.com/download

**Problem:** `API key errors`
- **Solution:** Run `pradysagi configure` or edit `.env` file

**Problem:** `Port 8000 already in use`
- **Solution:** `pradysagi server --port 9000`

For more issues, see **INSTALLATION_AND_DEPLOYMENT_GUIDE.md**.

---

## 🎉 Next Steps

1. ✅ **Quick Start** (you are here)
2. 📖 **Read Documentation** - See full guides above
3. 🧪 **Try Commands** - Test `chat`, `agent`, `server`
4. ⚙️ **Configure** - Add API keys if needed
5. 🚀 **Deploy** - Push to cloud when ready

---

## 📞 Support

- **Issues**: https://github.com/prady/pradysagican/issues
- **Email**: f20240323@dubai.bits-pilani.ac.in
- **GitHub**: https://github.com/prady/pradysagican

---

## 📋 What's Included

- ✅ ModelRouter (4 LLM backends)
- ✅ MCPManager (14+ tools)
- ✅ RAGEngine (hybrid search)
- ✅ FastAPI Server (REST + WebSocket)
- ✅ CLI Tool (6 commands)
- ✅ Installation scripts
- ✅ Complete documentation
- ✅ Production deployment ready

---

**Ready to go? Start with:**

```bash
cd pradysagican
./install.sh
pradysagi chat
```

**The superintelligent agent system awaits!** 🚀

---

*Version: 6.0.0*  
*Status: Production Ready ✅*  
*Last Updated: March 28, 2026*
