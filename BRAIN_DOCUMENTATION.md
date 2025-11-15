# Ollama Brain System - Documentation

**System:** Delta HPC Cluster  
**Created:** November 14, 2025  
**Author:** Sushant Sharma (ssewuna123@gmail.com)  
**Version:** 1.0

---

## Overview

This document describes the Ollama Brain system — a multi-GPU AI infrastructure designed for code analysis, error debugging, and intelligent assistance. The system runs three language models across three dedicated GPUs, providing fast, reliable AI responses for development tasks.

---

## System Architecture

### Hardware Configuration
- **Server:** Delta HPC Cluster (delta.cs.uwindsor.ca)
- **GPUs:** 4× NVIDIA A16 (15GB each)
- **GPU Allocation:**
  - GPU 0: Available for other tasks
  - GPU 1: Dedicated to 14B model (Port 11436)
  - GPU 2: Dedicated to 7B model (Port 11435)
  - GPU 3: Dedicated to 3B model (Port 11434)

### Software Stack
- **Platform:** Ollama v0.12.11
- **CUDA Version:** 12.2
- **Library Path:** `/usr/lib/x86_64-linux-gnu/nvidia/current` and `/usr/local/cuda-12.3/lib64`
- **Process Manager:** GNU Screen

---

## Model Configuration

### Available Models

| Model Name    | Parameters | GPU   | Port  | Memory | Response Time | Best For |
|---------------|-----------|-------|--------|---------|----------------|----------|
| qwen2.5:3b    | 3B        | GPU 3 | 11434 | 2.5 GB | ~6 sec        | Simple queries, quick answers |
| qwen2.5:7b    | 7B        | GPU 2 | 11435 | 4.9 GB | ~8 sec        | Error analysis, code review |
| qwen2.5:14b   | 14B       | GPU 1 | 11436 | 9.6 GB | ~18 sec       | Optimization, architecture |

### Model Lifecycle
- **Keep-Alive Duration:** 15 minutes  
- **Auto-Unload:** After 15 minutes of inactivity  
- **Auto-Load:** Reloads automatically on new request  
- **Concurrency:** Each model handles requests independently  

---

## Installation Details

### Directory Structure
```
~/ollama-bin/
├── bin/
│   └── ollama
├── lib/
│   └── ollama/
│       ├── cuda_v12/
│       ├── cuda_v13/
│       └── libggml-*.so
~/.ollama/
└── models/

~/start-ollama.sh
~/brain_api.py
~/ollama-startup.log
~/BRAIN_DOCUMENTATION.md
```

### Environment Variables
```
LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/nvidia/current:/usr/local/cuda-12.3/lib64
OLLAMA_HOST=0.0.0.0:[port]
OLLAMA_KEEP_ALIVE=15m
CUDA_VISIBLE_DEVICES=[gpu_number]
```

---

## Usage Guide

### Command Line Interface

**Basic Syntax:**
```
OLLAMA_HOST=localhost:[port] ollama run [model] "[prompt]"
```

**Examples:**

Fast queries (3B – GPU 3)
```
OLLAMA_HOST=localhost:11434 ollama run qwen2.5:3b "What is 25 * 4?"
```

Balanced queries (7B – GPU 2)
```
OLLAMA_HOST=localhost:11435 ollama run qwen2.5:7b "Explain this error: IndexError"
```

Complex queries (14B – GPU 1)
```
OLLAMA_HOST=localhost:11436 ollama run qwen2.5:14b "Optimize this algorithm"
```

---

## Python API

**Installation:**
```
pip install requests
```

**Basic Usage:**
```python
from brain_api import Brain

brain = Brain(host="localhost")

answer = brain.ask("What is Python?", mode="fast")

fix = brain.analyze_error(
    error_msg="ZeroDivisionError: division by zero",
    code="result = 10 / 0"
)

explanation = brain.explain_code(
    code="def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
)

optimized = brain.optimize_code(
    code="your_code_here",
    mode="smart"
)
```

**Mode Selection:**
- `fast` → 3B (GPU 3)
- `balanced` → 7B (GPU 2)
- `smart` → 14B (GPU 1)

---

## HTTP REST API

**Endpoint Format:**
```
POST http://localhost:[port]/api/generate
Content-Type: application/json
```

**Request Example:**
```
{
  "model": "qwen2.5:7b",
  "prompt": "Your question here",
  "stream": false
}
```

**cURL Example:**
```
curl -X POST http://localhost:11435/api/generate \
-H "Content-Type: application/json" \
-d '{
  "model": "qwen2.5:7b",
  "prompt": "Explain inheritance in Python",
  "stream": false
}'
```

---

## System Administration

### Starting the System
```
~/start-ollama.sh
```

**Check running sessions:**
```
screen -ls
nvidia-smi
curl http://localhost:11434/api/version
```

### Stopping the System
```
screen -X -S ollama-3b quit
screen -X -S ollama-7b quit
screen -X -S ollama-14b quit
```

### Restarting the System
```
pkill -f ollama
screen -wipe
sleep 2
~/start-ollama.sh
```

### Monitoring
```
watch -n 1 nvidia-smi
cat ~/ollama-startup.log
screen -r ollama-7b
```

---

## Automatic Startup

### Crontab
```
crontab -l
```

Expected:
```
@reboot ~/start-ollama.sh
```

---

## Troubleshooting

### System Not Responding
```
screen -ls
nvidia-smi | grep ollama
pkill -f ollama
~/start-ollama.sh
```

### Port Already in Use
```
lsof -i :11434
pkill -f ollama
```

### GPU Issues
```
nvidia-smi
lsmod | grep nvidia_uvm
echo $LD_LIBRARY_PATH
```

---

## Performance Guidelines

### Model Choice
- **3B:** Fast, simple queries  
- **7B:** Default – debugging, explanations  
- **14B:** Heavy optimization, deep analysis  

### Speed
- 3B → ~5–8 sec  
- 7B → ~7–12 sec  
- 14B → ~15–25 sec  

---

## Security Considerations

### Bind to Localhost Only  
Change:
```
OLLAMA_HOST=0.0.0.0:11434
```
To:
```
OLLAMA_HOST=127.0.0.1:11434
```

### SSH Tunnel:
```
ssh -L 11435:localhost:11435 sharmas1@delta.cs.uwindsor.ca
```

---

## Maintenance

### Weekly
```
tail -50 ~/ollama-startup.log
nvidia-smi
df -h ~
```

### Model Management
```
ollama pull llama3.2:3b
ollama rm model_name
ollama list
```

---

## Quick Reference

**Test models:**
```
OLLAMA_HOST=localhost:11434 ollama run qwen2.5:3b "test"
OLLAMA_HOST=localhost:11435 ollama run qwen2.5:7b "test"
OLLAMA_HOST=localhost:11436 ollama run qwen2.5:14b "test"
```

**Ports:**
- 11434 → 3B  
- 11435 → 7B  
- 11436 → 14B  

**Files:**
- `~/ollama-bin/`
- `~/.ollama/models/`
- `~/start-ollama.sh`
- `~/brain_api.py`
- `~/ollama-startup.log`
- `~/BRAIN_DOCUMENTATION.md`

---

## Support

- **Admin:** Sushant Sharma  
- **Email:** ssewuna123@gmail.com  
- **Server:** delta.cs.uwindsor.ca  

### Change Log
**v1.0 – Nov 14, 2025**
- Initial deployment  
- Multi-GPU setup  
- Auto-start enabled  
- Python API wrapper  

---

**Document Last Updated:** November 14, 2025, 6:17 PM EST
