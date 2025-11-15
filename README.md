# Project Synth - Delta Brain Client

A Python client for connecting to the Delta HPC Brain system at the University of Windsor. Provides easy access to three Ollama models (3B, 7B, 14B) running on GPU nodes via SSH tunneling.

## Features

- 🚀 Easy access to 3 Ollama models with different performance characteristics
- 🔐 Secure SSH key-based authentication
- 🔄 Auto-reconnecting SSH tunnel via macOS LaunchAgent
- 🧠 Simple Python API for code analysis, debugging, and AI queries
- ⚡ Multiple model modes: fast (3B), balanced (7B), smart (14B)

## Quick Start

### Prerequisites

- macOS
- Python 3.8+
- SSH access to delta.cs.uwindsor.ca
- SSH key pair (ed25519 recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sushantsharma22/Project-Synth.git
cd Project-Synth
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up SSH key (if not already done):
```bash
./generate_ssh_key.sh
# Follow prompts to copy public key to Delta server
```

5. Test connection:
```bash
python3 check_brain.py
```

## Usage

### Python API

```python
from brain_client import DeltaBrain

brain = DeltaBrain()

# Quick question (uses fast 3B model)
response = brain.ask("What is Python?")
print(response)

# Use smarter model for complex tasks
response = brain.ask("Explain quantum computing", mode="smart")
print(response)

# Analyze errors
analysis = brain.analyze_error(
    "ZeroDivisionError: division by zero",
    "def divide(a, b): return a / b"
)

# Explain code
explanation = brain.explain_code(
    "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
)

# Review code
review = brain.review_code(your_code)
```

### Available Models

| Model | Size | Port | Response Time | Best For |
|-------|------|------|---------------|----------|
| qwen2.5:3b | 3B | 11434 | ~0.7s | Quick queries, simple tasks |
| qwen2.5:7b | 7B | 11435 | ~12-16s | Code analysis, debugging |
| qwen2.5:14b | 14B | 11436 | Variable | Complex reasoning, research |

### Commands

```bash
# Check connection status
python3 check_brain.py

# Run comprehensive tests
python3 test_brain.py

# View example usage
python3 examples.py
```

## Architecture

```
┌──────────────────────────────────────────┐
│ Your Mac (localhost)                     │
│                                          │
│  Python Scripts → localhost:11434 (3B)  │
│                → localhost:11435 (7B)    │
│                → localhost:11436 (14B)   │
│                                          │
│  SSH Tunnel (Auto-maintained)           │
└──────────────┬───────────────────────────┘
               │
               ↓ (encrypted SSH)
┌──────────────┴───────────────────────────┐
│ Delta HPC (delta.cs.uwindsor.ca)        │
│                                          │
│  Ollama on GPU 3 → localhost:11434      │
│  Ollama on GPU 2 → localhost:11435      │
│  Ollama on GPU 1 → localhost:11436      │
└──────────────────────────────────────────┘
```

## Project Structure

```
Project-Synth/
├── brain_client.py          # Main Python API
├── test_brain.py            # Test suite
├── check_brain.py           # Connection checker
├── examples.py              # Usage examples
├── generate_ssh_key.sh      # SSH key setup helper
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── ROADMAP.md              # Development roadmap
├── BRAIN_DOCUMENTATION.md  # Brain system details
└── src/
    └── senses/             # Phase 1: Detection modules
        ├── clipboard_monitor.py
        ├── screen_capture.py
        └── __init__.py
```

## API Reference

### DeltaBrain Class

#### Methods

- `ask(prompt, mode='fast')` - Ask a question
  - `mode`: 'fast' (3B), 'balanced' (7B), 'smart' (14B)

- `analyze_error(error_msg, code, mode='balanced')` - Analyze error messages

- `explain_code(code, mode='balanced')` - Get code explanations

- `optimize_code(code, mode='balanced')` - Get optimization suggestions

- `review_code(code, mode='balanced')` - Get code review

- `check_connection()` - Check if models are accessible

## Troubleshooting

### Connection Issues

1. **Check if tunnel is running:**
```bash
lsof -nP -iTCP:11434,11435,11436 -sTCP:LISTEN
```

2. **Test SSH connection:**
```bash
ssh sharmas1@delta.cs.uwindsor.ca
```

3. **Run diagnostics:**
```bash
python3 check_brain.py
```

### Common Problems

**Q: Connection refused on localhost ports**  
A: Ensure SSH tunnel is running. Check logs or restart the tunnel.

**Q: SSH key authentication fails**  
A: Verify your public key is in `~/.ssh/authorized_keys` on Delta server.

**Q: Slow response times**  
A: Try a different model mode. 3B is fastest, 14B is slowest but most capable.

## Development

### Running Tests
```bash
python3 test_brain.py
```

### Phase 1 Features (In Progress)
- Clipboard monitoring for error detection
- Screen capture for UI error detection
- Automatic error analysis workflow

See `ROADMAP.md` for planned features.

## Security

- Uses SSH key-based authentication (no passwords stored)
- All traffic encrypted via SSH tunnel
- Ports bound to localhost only (not exposed to network)
- Keys and sensitive configs excluded from version control

## Requirements

- Python 3.8+
- macOS (for LaunchAgent auto-connect)
- SSH access to delta.cs.uwindsor.ca
- Dependencies listed in `requirements.txt`

## Contributing

This is a personal project for University of Windsor students with access to the Delta HPC system. Feel free to fork and adapt for your own use.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- University of Windsor School of Computer Science
- Delta HPC System
- Ollama project

## Support

For Delta HPC access issues: http://help.cs.uwindsor.ca

---

**Status:** Production Ready ✅  
**Last Updated:** November 14, 2025
