# Project Synth

**Proactive AI Assistant for macOS - Zero Cost, Full Privacy**

<div align="center">

![Phase](https://img.shields.io/badge/Phase-0%20Complete-success)
![Status](https://img.shields.io/badge/Status-Phase%201%20Starting-blue)
![Cost](https://img.shields.io/badge/Cost-$0-brightgreen)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey)

</div>

---

## 🎯 What is Project Synth?

An intelligent, proactive AI assistant that:
- 📋 **Monitors** your clipboard and screen
- 🧠 **Understands** context using multi-GPU AI
- 💡 **Suggests** helpful actions proactively
- 🤖 **Automates** tasks with your permission

**All running on your hardware. Zero cloud. Zero cost. Full privacy.**

---

## 🏗️ Architecture

```
┌─────────────────┐         SSH Tunnel        ┌──────────────────┐
│  MacBook Air M3 │ ◄──────────────────────► │ Delta HPC Server │
│                 │                            │                  │
│  • Senses       │                            │  • 4× NVIDIA A16 │
│  • Hands        │                            │  • Ollama        │
│  • UI           │                            │  • 3 Models:     │
│                 │                            │    - 3B (fast)   │
│                 │                            │    - 7B (balanced)│
│                 │                            │    - 14B (smart) │
└─────────────────┘                            └──────────────────┘
```

**Client:** MacBook (detection, automation, UI)  
**Server:** Delta HPC (AI reasoning with multi-GPU)  
**Connection:** Encrypted SSH tunnel

---

## ✨ Current Status

### ✅ Phase 0: Infrastructure (COMPLETE)

- ✅ Delta Brain running 24/7
- ✅ Multi-GPU Ollama deployment (3B, 7B, 14B)
- ✅ SSH tunnel connection
- ✅ Python client library
- ✅ Local development environment

### 🔄 Phase 1: Senses (STARTING)

Building the detection system for clipboard and screen monitoring.

**See full roadmap:** [`ROADMAP.md`](ROADMAP.md)

---

## 🚀 Quick Start

### Prerequisites

- macOS 11+ (M1/M2/M3 or Intel)
- Python 3.11+
- Access to Delta HPC server (or your own Ollama server)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/project-synth.git
cd project-synth

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Connect to Delta Brain
./connect_brain.sh

# Test connection
python test_brain.py
```

---

## 📖 Documentation

- **[Roadmap](ROADMAP.md)** - Complete development plan (10-12 weeks)
- **[Quick Reference](QUICK_REFERENCE.md)** - Brain client API reference
- **[Brain Documentation](BRAIN_DOCUMENTATION.md)** - Delta HPC system details
- **[Examples](examples.py)** - Usage examples

---

## 🎬 Demo Scenario (Phase 2 Target)

**Situation:** You're coding and encounter a `KeyError`

1. **Senses:** Project Synth detects the error in your editor
2. **Brain:** Analyzes the code context and error
3. **Suggestion:** Sends notification: "Add error handling for missing key?"
4. **Hands:** Click "Yes" → Code automatically updated

**All in <3 seconds.**

---

## 🏛️ Project Structure

```
project-synth/
├── src/
│   ├── senses/          # 👀 Phase 1: Clipboard & screen detection
│   ├── brain/           # 🧠 Phase 2: AI reasoning & prompts
│   ├── hands/           # 🤖 Phase 3: Automation & execution
│   └── ui/              # 🎨 Phase 3: Menu bar application
├── brain_client/        # ✅ Delta Brain connection library
│   ├── brain_client.py
│   ├── test_brain.py
│   └── examples.py
├── tests/               # 🧪 Test suites
├── docs/                # 📚 Documentation
├── examples/            # 💡 Usage examples
└── config/              # ⚙️ Configuration files
```

---

## 🛠️ Tech Stack

**Client (MacBook):**
- Python 3.11+
- `rumps` - Menu bar UI
- `mss` - Screen capture
- `PyObjC` - macOS integration
- `pyperclip` - Clipboard monitoring

**Server (Delta HPC):**
- Ollama - LLM inference
- Qwen2.5 (3B, 7B, 14B) - Language models
- CUDA 12.2 - GPU acceleration
- systemd - Service management

**Cost:** $0 (100% open-source stack)

---

## 📊 Roadmap Progress

| Phase | Status | Timeline |
|-------|--------|----------|
| **0: Infrastructure** | ✅ Complete | Week 1 |
| **1: Senses** | 🔄 Current | Week 2 |
| **2: Brain** | ⏳ Pending | Week 3 |
| **3: Hands** | ⏳ Pending | Weeks 4-5 |
| **4: Polish** | ⏳ Pending | Weeks 6-7 |
| **5: Advanced** | ⏳ Pending | Weeks 8-10 |
| **6: Launch** | ⏳ Pending | Weeks 11-12 |

**Target Launch:** v1.0 in 12 weeks

---

## 🎯 Success Metrics

- ⏱️ **Response Time:** <3 seconds (detection → notification)
- 🎯 **Accuracy:** >80% (suggestions accepted)
- 🔋 **Battery Impact:** <5% additional drain
- ⚡ **Uptime:** >99% (server availability)

---

## 🤝 Contributing

This project is currently in active development (Phase 0-1). Contributions will be welcome after Phase 6 (public launch).

**Interested in contributing?**
- ⭐ Star this repo to follow progress
- 👀 Watch for v1.0 release
- 💬 Join discussions in Issues

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **University of Windsor** - Delta HPC cluster access
- **Ollama Team** - Amazing local LLM platform
- **Qwen Team** - Excellent open-source models

---

## 👤 Author

**Sushant Sharma**  
📧 ssewuna123@gmail.com  
🏫 University of Windsor  
🖥️ Delta HPC Cluster

---

## 📈 Vision

**Short-term:** Functional proactive assistant for macOS  
**Medium-term:** Cross-platform support (Windows, Linux)  
**Long-term:** Plugin marketplace, enterprise features, custom model fine-tuning

---

<div align="center">

**Built with ❤️ on $0 budget**

[Roadmap](ROADMAP.md) • [Documentation](BRAIN_DOCUMENTATION.md) • [Quick Start](#-quick-start)

</div>
