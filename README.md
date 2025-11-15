# Project Synth# Project Synth - Delta Brain Client



**An intelligent AI-powered assistant for macOS with screen analysis, natural language processing, and extensible plugin architecture.**A Python client for connecting to the Delta HPC Brain system at the University of Windsor. Provides easy access to three Ollama models (3B, 7B, 14B) running on GPU nodes via SSH tunneling.



[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)## Features

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)- 🚀 Easy access to 3 Ollama models with different performance characteristics

- 🔐 Secure SSH key-based authentication

---- 🔄 Auto-reconnecting SSH tunnel via macOS LaunchAgent

- 🧠 Simple Python API for code analysis, debugging, and AI queries

## Overview- ⚡ Multiple model modes: fast (3B), balanced (7B), smart (14B)



Project Synth is a native macOS menu bar application that provides intelligent AI assistance through:## Quick Start



- **Screen Analysis**: OCR-based screen content extraction and AI-powered understanding### Prerequisites

- **Natural Language Processing**: Context-aware responses using large language models

- **Plugin System**: Extensible architecture with 8+ built-in plugins- macOS

- **Native Integration**: Seamless macOS experience with system-level clipboard and UI integration- Python 3.8+

- SSH access to delta.cs.uwindsor.ca

## Features- SSH key pair (ed25519 recommended)



### Core Capabilities### Installation



- 🧠 **AI-Powered Queries**: Ask questions and get intelligent responses1. Clone the repository:

- 📸 **Screen Understanding**: Analyze screen content with OCR and AI```bash

- 🔌 **Plugin Ecosystem**: Email drafting, web search, file management, code analysis, and moregit clone https://github.com/sushantsharma22/Project-Synth.git

- 📋 **Clipboard Integration**: Automatic context detection from clipboardcd Project-Synth

- ⚡ **Multi-Model Support**: Fast (3B), balanced (7B), and smart (14B) AI models```

- 🎯 **Menu Bar Access**: Always-available native macOS interface

2. Create virtual environment:

### Built-in Plugins```bash

python3 -m venv venv

1. **Email Plugin** - Draft professional emails from screen contentsource venv/bin/activate

2. **Web Search** - Intelligent search query generation and browser integration```

3. **File Management** - File operations and organization assistance

4. **Code Documentation** - Code analysis and documentation generation3. Install dependencies:

5. **Security Tools** - Security scanning and best practices```bash

6. **Math Calculator** - Advanced mathematical computationspip install -r requirements.txt

7. **Calendar** - Meeting scheduling and calendar management```

8. **Git Helper** - Git commands and workflow assistance

4. Set up SSH key (if not already done):

## Installation```bash

./generate_ssh_key.sh

### Prerequisites# Follow prompts to copy public key to Delta server

```

- macOS 10.15 or later

- Python 3.8 or higher5. Test connection:

- Tesseract OCR (for screen analysis)```bash

python3 check_brain.py

### Setup```



1. **Clone the repository**:## Usage

   ```bash

   git clone https://github.com/sushantsharma22/Project-Synth.git### Python API

   cd Project-Synth

   ``````python

from brain_client import DeltaBrain

2. **Create virtual environment**:

   ```bashbrain = DeltaBrain()

   python3 -m venv venv

   source venv/bin/activate# Quick question (uses fast 3B model)

   ```response = brain.ask("What is Python?")

print(response)

3. **Install dependencies**:

   ```bash# Use smarter model for complex tasks

   pip install -r requirements.txtresponse = brain.ask("Explain quantum computing", mode="smart")

   ```print(response)



4. **Install Tesseract OCR** (required for screen analysis):# Analyze errors

   ```bashanalysis = brain.analyze_error(

   brew install tesseract    "ZeroDivisionError: division by zero",

   ```    "def divide(a, b): return a / b"

)

5. **Launch the application**:

   ```bash# Explain code

   python synth_native.pyexplanation = brain.explain_code(

   ```    "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"

)

## Usage

# Review code

### Quick Startreview = brain.review_code(your_code)

```

1. **Launch Synth**: Run `python synth_native.py` - the icon appears in your menu bar

2. **Ask a Question**: Click the Synth icon, type your query, and press Ask### Available Models

3. **Screen Analysis**: Enable the 📸 Screen checkbox to analyze screen content with your query

4. **Use Plugins**: Click on ⚙️ Plugins & Settings to explore available plugins| Model | Size | Port | Response Time | Best For |

|-------|------|------|---------------|----------|

### Example Queries| qwen2.5:3b | 3B | 11434 | ~0.7s | Quick queries, simple tasks |

| qwen2.5:7b | 7B | 11435 | ~12-16s | Code analysis, debugging |

- `"Explain quantum computing"`| qwen2.5:14b | 14B | 11436 | Variable | Complex reasoning, research |

- `"How do I use async/await in Python?"`

- With screen analysis enabled: `"Draft an email reply to this"`### Commands

- `"What's on my screen?"`

```bash

### Keyboard Shortcuts# Check connection status

python3 check_brain.py

- **Enter/Return**: Submit query

- **Cmd+C**: Copy output text# Run comprehensive tests

- **Cmd+V**: Paste into input fieldpython3 test_brain.py

- **Clear Button**: Reset interface

# View example usage

## Architecturepython3 examples.py

```

```

Project-Synth/## Architecture

├── synth_native.py              # Main menu bar application

├── brain_client.py              # AI model client```

├── requirements.txt             # Python dependencies┌──────────────────────────────────────────┐

├── src/│ Your Mac (localhost)                     │

│   ├── brain/│                                          │

│   │   └── brain_api_client.py  # Brain API interface│  Python Scripts → localhost:11434 (3B)  │

│   ├── hands/│                → localhost:11435 (7B)    │

│   │   ├── action_executors.py  # Action execution engine│                → localhost:11436 (14B)   │

│   │   └── action_manager.py    # Action coordination│                                          │

│   ├── senses/│  SSH Tunnel (Auto-maintained)           │

│   │   ├── clipboard_monitor.py # Clipboard detection└──────────────┬───────────────────────────┘

│   │   ├── screen_capture.py    # Screen capture utility               │

│   │   ├── ocr_engine.py        # OCR processing               ↓ (encrypted SSH)

│   │   └── trigger_system.py    # Event triggers┌──────────────┴───────────────────────────┐

│   └── plugins/│ Delta HPC (delta.cs.uwindsor.ca)        │

│       ├── base_plugin.py       # Plugin base class│                                          │

│       ├── plugin_manager.py    # Plugin loader│  Ollama on GPU 3 → localhost:11434      │

│       └── core/                # Built-in plugins│  Ollama on GPU 2 → localhost:11435      │

│           ├── email_plugin.py│  Ollama on GPU 1 → localhost:11436      │

│           ├── web_search_plugin.py└──────────────────────────────────────────┘

│           ├── file_management_plugin.py```

│           ├── code_doc_plugin.py

│           ├── security_plugin.py## Project Structure

│           ├── math_plugin.py

│           ├── calendar_plugin.py```

│           └── git_plugin.pyProject-Synth/

└── LICENSE├── brain_client.py          # Main Python API

```├── test_brain.py            # Test suite

├── check_brain.py           # Connection checker

## System Requirements├── examples.py              # Usage examples

├── generate_ssh_key.sh      # SSH key setup helper

### Hardware├── requirements.txt         # Python dependencies

├── README.md                # This file

- Mac with Apple Silicon or Intel processor├── ROADMAP.md              # Development roadmap

- 4GB+ RAM recommended├── BRAIN_DOCUMENTATION.md  # Brain system details

- Internet connection for AI model access└── src/

    └── senses/             # Phase 1: Detection modules

### Software        ├── clipboard_monitor.py

        ├── screen_capture.py

- macOS 10.15 (Catalina) or later        └── __init__.py

- Python 3.8+```

- Tesseract OCR 4.0+

## API Reference

## Configuration

### DeltaBrain Class

### AI Models

#### Methods

The application uses three model tiers:

- `ask(prompt, mode='fast')` - Ask a question

| Model | Size | Use Case | Response Time |  - `mode`: 'fast' (3B), 'balanced' (7B), 'smart' (14B)

|-------|------|----------|---------------|

| Fast | 3B | Quick queries, simple tasks | ~1s |- `analyze_error(error_msg, code, mode='balanced')` - Analyze error messages

| Balanced | 7B | General purpose, default | ~5-8s |

| Smart | 14B | Complex reasoning, analysis | ~15-20s |- `explain_code(code, mode='balanced')` - Get code explanations



Models are configured in `brain_client.py` and can be customized based on your infrastructure.- `optimize_code(code, mode='balanced')` - Get optimization suggestions



## Development- `review_code(code, mode='balanced')` - Get code review



### Plugin Development- `check_connection()` - Check if models are accessible



Create custom plugins by extending the `BasePlugin` class:## Troubleshooting



```python### Connection Issues

from src.plugins.base_plugin import BasePlugin, PluginMetadata, PluginContext, PluginSuggestion

1. **Check if tunnel is running:**

class MyPlugin(BasePlugin):```bash

    def _get_metadata(self):lsof -nP -iTCP:11434,11435,11436 -sTCP:LISTEN

        return PluginMetadata(```

            name="my_plugin",

            version="1.0.0",2. **Test SSH connection:**

            author="Your Name",```bash

            description="Plugin description"ssh sharmas1@delta.cs.uwindsor.ca

        )```

    

    def can_handle(self, context: PluginContext) -> bool:3. **Run diagnostics:**

        # Return True if plugin can handle this context```bash

        return Truepython3 check_brain.py

    ```

    def analyze(self, context: PluginContext) -> list[PluginSuggestion]:

        # Return list of suggestions### Common Problems

        return []

```**Q: Connection refused on localhost ports**  

A: Ensure SSH tunnel is running. Check logs or restart the tunnel.

### Contributing

**Q: SSH key authentication fails**  

Contributions are welcome! Please:A: Verify your public key is in `~/.ssh/authorized_keys` on Delta server.



1. Fork the repository**Q: Slow response times**  

2. Create a feature branchA: Try a different model mode. 3B is fastest, 14B is slowest but most capable.

3. Make your changes with clear commit messages

4. Test thoroughly## Development

5. Submit a pull request

### Running Tests

## Security```bash

python3 test_brain.py

- SSH key-based authentication (no stored passwords)```

- All AI traffic encrypted via SSH tunnels

- Localhost-only port bindings### Phase 1 Features (In Progress)

- No sensitive data logged or transmitted- Clipboard monitoring for error detection

- `.gitignore` configured to exclude credentials and personal data- Screen capture for UI error detection

- Automatic error analysis workflow

## Troubleshooting

See `ROADMAP.md` for planned features.

### Common Issues

## Security

**App doesn't appear in menu bar**:

- Ensure PyObjC is installed: `pip install pyobjc`- Uses SSH key-based authentication (no passwords stored)

- Check terminal for error messages- All traffic encrypted via SSH tunnel

- Ports bound to localhost only (not exposed to network)

**Screen analysis not working**:- Keys and sensitive configs excluded from version control

- Verify Tesseract installation: `tesseract --version`

- Install with: `brew install tesseract`## Requirements



**Copy/paste not working**:- Python 3.8+

- Click in the text area to focus- macOS (for LaunchAgent auto-connect)

- Use native macOS shortcuts (Cmd+C, Cmd+V)- SSH access to delta.cs.uwindsor.ca

- Dependencies listed in `requirements.txt`

**Plugins not loading**:

- Check plugin files exist in `src/plugins/core/`## Contributing

- Verify Python syntax with `python -m py_compile <plugin_file>`

This is a personal project for University of Windsor students with access to the Delta HPC system. Feel free to fork and adapt for your own use.

## License

## License

MIT License - see [LICENSE](LICENSE) file for details.

MIT License - See LICENSE file for details

## Acknowledgments

---

- Built with [PyObjC](https://pyobjc.readthedocs.io/) for native macOS integration

- OCR powered by [Tesseract](https://github.com/tesseract-ocr/tesseract)**Status:** Production Ready ✅  

- AI models hosted on Delta HPC infrastructure**Last Updated:** November 14, 2025


---

**Project Status**: Active Development  
**Version**: 1.0.0  
**Last Updated**: November 2025

For questions or support, please open an issue on GitHub.
