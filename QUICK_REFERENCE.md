# Delta Brain - Quick Reference Card

## 🔌 Connect to Brain

```bash
./connect_brain.sh
# OR manually:
ssh -L 11434:localhost:11434 -L 11435:localhost:11435 -L 11436:localhost:11436 sharmas1@delta.cs.uwindsor.ca
```

Keep SSH terminal open!

---

## 🐍 Python Quick Start

```python
from brain_client import DeltaBrain

brain = DeltaBrain()
```

---

## 📋 Core Methods

### Ask Questions
```python
answer = brain.ask("Your question here", mode="balanced")
```

### Debug Errors
```python
fix = brain.analyze_error(
    error_msg="Error message",
    code="your code"
)
```

### Explain Code
```python
explanation = brain.explain_code("code snippet")
```

### Optimize Code
```python
optimized = brain.optimize_code("slow code", mode="smart")
```

### Review Code
```python
review = brain.review_code("code to review")
```

### Check Status
```python
status = brain.check_connection()
```

---

## 🎯 Model Modes

| Mode | Speed | Use For |
|------|-------|---------|
| `fast` | ~6s | Quick questions, simple tasks |
| `balanced` | ~8s | Error analysis, explanations (DEFAULT) |
| `smart` | ~18s | Optimization, complex analysis |

---

## 🧪 Test Commands

```bash
# Test connection
python test_brain.py

# See examples
python examples.py

# Direct test
python brain_client.py
```

---

## 🔍 Common Use Cases

### Debug a Python Error
```python
code = """
def process(items):
    return items[0]
    
result = process([])
"""

fix = brain.analyze_error("IndexError: list index out of range", code)
print(fix)
```

### Understand Complex Code
```python
complex = "lambda x: reduce(lambda a,b: a*b, range(1,x+1))"
explanation = brain.explain_code(complex)
print(explanation)
```

### Optimize Slow Function
```python
slow = """
def sum_all(n):
    total = 0
    for i in range(n):
        total += i
    return total
"""

better = brain.optimize_code(slow, mode="smart")
print(better)
```

---

## 🚨 Troubleshooting

**"Connection Error"**
→ Run `./connect_brain.sh` first

**"Not reachable"**
→ Check Brain is running on Delta: `screen -ls`

**Timeout**
→ Use faster mode or wait (Brain auto-loads models)

---

## 📂 Project Files

- `brain_client.py` - Main client library
- `test_brain.py` - Connection tests
- `examples.py` - Usage examples
- `connect_brain.sh` - SSH tunnel helper
- `BRAIN_DOCUMENTATION.md` - Full docs
- `QUICK_REFERENCE.md` - This file

---

## 💡 Tips

1. **Always use SSH tunnel** before running code
2. **Start with `balanced` mode** for most tasks
3. **Use `fast` mode** for quick iterations
4. **Use `smart` mode** for optimization/architecture
5. **Check connection** with `check_connection()` if unsure

---

## 🔗 SSH Tunnel Ports

- **11434** → 3B model (fast)
- **11435** → 7B model (balanced)
- **11436** → 14B model (smart)

---

## 👤 Support

**Author:** Sushant Sharma  
**Email:** ssewuna123@gmail.com  
**Server:** delta.cs.uwindsor.ca  

---

**Quick copy-paste:**
```bash
# Terminal 1: Connect
./connect_brain.sh

# Terminal 2: Activate & Test
cd "project synth"
source venv/bin/activate
python test_brain.py
```
