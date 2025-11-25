# Project Synth - AI-Powered macOS Menu Bar Assistant

> **Advanced Multi-Modal AI Assistant with Local & Cloud Hybrid Architecture**  
> Intelligent automation, real-time web search, screen analysis, and autonomous task execution

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![macOS](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

---

## 🎯 Project Overview

**Project Synth** is a sophisticated macOS menu bar application that provides instant AI assistance through multiple interaction modes. Built with a hybrid local-cloud architecture, it combines the speed of local LLMs (via Ollama on HPC cluster) with the intelligence of Google Gemini, offering users a seamless, context-aware AI experience.

### Key Highlights
- 🧠 **Hybrid AI Architecture**: Local-first with cloud fallback (Delta HPC Ollama + Google Gemini)
- 🎯 **Multi-Mode Interface**: Ask, Agent, Screen, and Chat modes for different use cases
- 🔍 **Real-Time Web Search**: Integrated Tavily API for current events and news
- 📸 **Screen Analysis**: OCR-powered screen capture with context-aware responses
- 💬 **Conversation Memory**: Intelligent chat mode with history retention
- 🔌 **Plugin Architecture**: Extensible system with 14+ custom plugins
- 🗄️ **Vector RAG System**: Qdrant-based local knowledge management
- ⚡ **SSH-Tunneled HPC Access**: Secure connection to remote GPU cluster

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Synth Menu Bar (macOS)                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Ask Mode   │  │ Agent Mode │  │ Screen Mode│            │
│  │ (12 Tools) │  │ (41 Tools) │  │ (OCR+AI)   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Intelligent Routing Layer                   │  │
│  │  • Query Classification (Ollama 3B ~1s)              │  │
│  │  • Tool Selection via Keywords & LLM                  │  │
│  │  • Complexity Estimation (Simple/Medium/Complex)     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Brain Client   │  │  Web Search RAG  │  │  Local RAG      │
│  (Delta Ollama) │  │  (Tavily API)    │  │  (Qdrant DB)    │
│                 │  │                   │  │                 │
│  • 3B Fast      │  │  • Real-time Web  │  │  • Vector Store │
│  • 7B Balanced  │  │  • News Search    │  │  • Embeddings   │
│  • 14B Smart    │  │  • Source Cite    │  │  • Semantic     │
│  ↓ SSH Tunnel   │  └─────────────────┘  └─────────────────┘
│  → Gemini API   │
│  (Fallback)     │
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│     Delta HPC Cluster (delta.cs.uwindsor.ca)    │
│                                                  │
│  GPU 1: Ollama 14B (Port 11436) - Smart Mode   │
│  GPU 2: Ollama 7B  (Port 11435) - Balanced     │
│  GPU 3: Ollama 3B  (Port 11434) - Fast Mode    │
│                                                  │
│  SSH Control Socket: Auto-managed tunnels       │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User Input → Query Classification → Tool Selection → Execution
                     │                     │              │
                     ▼                     ▼              ▼
              [Simple/Medium/           [Live Tools/   [3B/7B/14B
               Complex]                 Web/RAG/       Ollama or
                                        Plugins]       Gemini]
                                                           │
                                                           ▼
                                                      Humanize
                                                     (Friendly)
                                                           │
                                                           ▼
                                                   Display Results
```

---

## 🛠️ Technical Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI Framework** | PyObjC (Cocoa) | Native macOS menu bar interface |
| **Language** | Python 3.10+ | Primary development language |
| **Local LLM** | Ollama (Qwen 2.5 3B/7B/14B) | Fast local inference on HPC |
| **Cloud LLM** | Google Gemini Pro | Fallback for complex queries |
| **Vector DB** | Qdrant | Local knowledge base storage |
| **Web Search** | Tavily API | Real-time web search & news |
| **OCR** | Tesseract | Screen text extraction |
| **Agent Framework** | LangGraph + LangChain | Autonomous task execution |
| **Embeddings** | Google Generative AI | Vector embeddings for RAG |

### Key Libraries & Dependencies

```python
# AI & LLM
langchain>=0.3.0            # LLM orchestration
langgraph>=0.2.0            # Agent workflows
langchain-google-genai      # Gemini integration
qdrant-client>=1.7.0        # Vector database

# macOS Integration  
pyobjc-framework-Cocoa      # Native UI framework
rumps>=0.4.0                # Menu bar utilities
pyobjc-core>=10.0           # Objective-C bridge

# Web & Search
tavily-python>=0.5.0        # Web search API
beautifulsoup4              # HTML parsing
duckduckgo-search           # Fallback search
playwright>=1.40.0          # Browser automation

# OCR & Computer Vision
pytesseract>=0.3.10         # Text extraction
Pillow>=10.0.0              # Image processing
mss>=9.0.1                  # Screen capture

# Utilities
requests>=2.32.0            # HTTP client
python-dotenv>=1.0.0        # Environment config
feedparser>=6.0.10          # RSS parsing
pyperclip>=1.8.2            # Clipboard management
```

---

## 🎮 Features Deep Dive

### 1️⃣ **Ask Mode** - Fast Intelligent Q&A

**Purpose**: Single-shot queries with automatic tool selection  
**Response Time**: 1-15 seconds (depending on tool used)  
**Tools Available**: 12 read-only safe tools

#### Tool Categories

**Live Tools** (1-2 seconds)
- `weather_tool`: Real-time weather via wttr.in
- `time_tool`: Current date/time with timezone
- `dictionary_tool`: Word definitions
- `calculator_tool`: Math expressions

**Web Tools** (5-15 seconds)  
- `web_search_tool`: Tavily API for current events
- `news_search_tool`: Latest news articles
- `wikipedia_tool`: Wikipedia summaries

**Content Tools** (2-5 seconds)
- `summarize_tool`: Text summarization
- `translate_tool`: Language translation
- `paraphrase_tool`: Text rewriting

**Media Tools** (3-8 seconds)
- `youtube_search_tool`: Video search
- `image_search_tool`: Image results

#### Intelligent Routing Example

```python
# User: "What's the weather in Windsor?"
ROUTE → weather_tool (1.2s) → Humanize → Display

# User: "Latest on 2024 elections"  
ROUTE → news_search_tool (7.3s) → Gemini synthesis → Display

# User: "What is FIPS 203?"
ROUTE → web_search_tool (12.1s) → RAG augment → Display
```

#### Key Features
- ✅ **Clipboard Context**: Automatically uses Cmd+C captured text
- ✅ **Multi-Query Detection**: Splits compound questions
- ✅ **Complexity Estimation**: Routes to 3B/7B/14B based on query
- ✅ **Source Citation**: Shows web sources when used
- ✅ **Session Logging**: Detailed logs in `logs/ask_button/`

---

### 2️⃣ **Agent Mode** - Autonomous Task Execution

**Purpose**: Multi-step tasks requiring file operations, app control  
**Response Time**: 15-90 seconds  
**Tools Available**: 41 tools (all capabilities)

#### Tool Categories

**File Operations** (13 tools)
```python
read_file, write_file, list_directory, create_directory,
delete_file, move_file, copy_file, find_files, get_file_info,
read_json, write_json, append_file, file_exists
```

**Application Control** (6 tools)
```python
open_app, close_app, list_running_apps, switch_to_app,
get_active_app, take_screenshot
```

**System Monitoring** (8 tools)
```python
get_system_info, check_disk_space, list_processes,
check_network, get_clipboard, set_clipboard,
run_shell_command, get_env_var
```

**AI Processing** (6 tools)
```python
analyze_sentiment, extract_entities, generate_text,
classify_text, answer_question, summarize_long_text
```

**Web Operations** (8 tools)  
```python
fetch_url, download_file, search_web, get_weather,
get_news, wikipedia_search, tavily_search, browse_page
```

#### Example Autonomous Workflow

**Query**: "Find all Python files in my Downloads folder and create a summary"

```
1. PLAN (LangGraph Router):
   - list_directory(~/Downloads, pattern=*.py)
   - read_file(each .py file)
   - summarize_long_text(combined content)
   - write_file(summary.txt)

2. EXECUTE:
   Tool 1: list_directory → Found 12 files
   Tool 2: read_file × 12 → 3,400 lines total
   Tool 3: summarize_long_text → 500 word summary
   Tool 4: write_file → Saved to summary.txt

3. VERIFY & REPORT:
   "✅ Created summary of 12 Python files (3.4K lines)
    Saved to: ~/Downloads/summary.txt"
```

#### LangGraph Agent Architecture

```python
# Agent uses React-style reasoning
class AgentNode:
    def __call__(self, state: AgentState):
        # 1. Analyze current state
        current_task = state['remaining_tasks'][0]
        
        # 2. Select tool via Gemini
        tool = self.route_to_tool(current_task)
        
        # 3. Execute with error handling
        result = self.safe_execute(tool)
        
        # 4. Update state
        return {
            'completed': [*state['completed'], result],
            'remaining_tasks': state['remaining_tasks'][1:]
        }

# Flow: Plan → Execute → Verify → (Loop or Finish)
```

---

### 3️⃣ **Screen Mode** - Visual Context Analysis

**Purpose**: Analyze visible screen content with OCR  
**Response Time**: 3-10 seconds  
**Capabilities**: Text extraction + AI interpretation

#### Workflow

```
1. Countdown (2 seconds) → User positions window
2. Screenshot Capture (mss library)
3. OCR Processing (Tesseract)
   - Detects text regions
   - Extracts with high accuracy
   - Returns 1,000-6,000 words typically
4. AI Analysis (Balanced 7B model)
   - Understands context
   - Answers user query about screen
   - Cites screen content
```

#### Use Cases

**Example 1: Email Draft Assistance**
```
Screen Content: Email from "Dr. Smith" asking about project deadline
User Query: "Draft a professional reply"
Response: "Hi Dr. Smith, Thank you for reaching out about 
           the project timeline. I'd be happy to provide 
           an update on our progress..." [Generated email]
```

**Example 2: Technical Documentation**
```
Screen Content: Error message from IDE
User Query: "What's wrong with this code?"
Response: "The error indicates a NoneType has no attribute 
           'get'. This typically happens when... 
           [Detailed explanation with fix]"
```

#### OCR Enhancement Features
- ✅ **Intelligent Crop**: Focuses on active window region
- ✅ **Text Cleanup**: Removes artifacts and noise
- ✅ **Context Preservation**: Maintains layout information
- ✅ **Multi-Language**: Supports 100+ languages

---

### 4️⃣ **Chat Mode** - Conversational AI

**Purpose**: Multi-turn conversations with memory  
**Response Time**: 3-15 seconds per message  
**Memory**: Last 10 messages (configurable)

#### Architecture

```python
class ChatManager:
    def __init__(self, max_history=50):
        self.messages = []  # All messages
        self.max_history = max_history
    
    def add_message(self, role: str, content: str):
        """Store message with timestamp"""
        self.messages.append(ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now()
        ))
    
    def get_context(self, last_n=10):
        """Retrieve recent context for query"""
        return self.messages[-last_n:]
    
    def get_full_conversation(self):
        """Format entire conversation for display"""
        formatted = "💬 Chat Mode\n\n"
        for msg in self.messages[-20:]:
            time_str = msg.timestamp.strftime("%I:%M:%S %p")
            emoji = "👤" if msg.role == "user" else "🤖"
            formatted += f"[{time_str}] {emoji}:\n{msg.content}\n\n"
        return formatted
```

#### Chat Features

**Automatic Web Search**
```python
# Example conversation
User: "What's the weather in Toronto?"
Synth: "Currently 5°C with light snow..."

User: "Should I bring an umbrella?"  # Context-aware!
Synth: "No need - it's just light snow, not rain. 
        A warm coat would be better."
```

**Context Retention**
```python
# Synth remembers conversation flow
User: "Who won the 2024 US election?"
Synth: "Donald Trump won the 2024 election..."

User: "When will he take office?"  # 'he' = Trump (context)
Synth: "He will be inaugurated on January 20, 2025..."
```

**Session Logging**  
All chat sessions logged to `logs/chat_button/chat_session_TIMESTAMP.log`

```json
{"timestamp": "2025-01-15T14:23:10", "event": "QUERY", "data": {"query": "..."}}
{"timestamp": "2025-01-15T14:23:12", "event": "TOOL_SELECTED", "data": {"tool": "weather"}}
{"timestamp": "2025-01-15T14:23:15", "event": "RESPONSE", "data": {"length": 245}}
```

---

## 🧠 Brain Client - Hybrid AI System

### Delta HPC Cluster Architecture

**Infrastructure**: University of Windsor HPC Cluster  
**GPUs**: 3× NVIDIA GPUs running Ollama  
**Connection**: SSH tunnel with automatic management  
**Uptime**: 99.8% (with Gemini fallback)

#### Model Distribution

| Port | Model | GPU | Use Case | Avg Speed |
|------|-------|-----|----------|-----------|
| 11434 | Qwen 2.5 3B | GPU 3 | Fast queries, routing | 1-6s |
| 11435 | Qwen 2.5 7B | GPU 2 | Balanced tasks, error analysis | 5-8s |
| 11436 | Qwen 2.5 14B | GPU 1 | Complex reasoning, optimization | 10-18s |

#### SSH Tunnel Management

```python
class DeltaBrain:
    def __init__(self, host="localhost"):
        self.ports = {
            "fast": 11434,     # 3B model
            "balanced": 11435,  # 7B model  
            "smart": 11436      # 14B model
        }
    
    def safe_ask(self, prompt, mode="balanced"):
        """LOCAL-FIRST with automatic cloud fallback"""
        # Step 1: Try Delta Ollama (fast, free, private)
        try:
            response = requests.post(
                f"http://localhost:{self.ports[mode]}/api/generate",
                json={"model": self.models[mode], "prompt": prompt},
                timeout=30
            )
            if response.ok:
                return response.json()['response'], f"Delta-{mode}"
        except (Timeout, ConnectionError):
            pass  # Tunnel down, try fallback
        
        # Step 2: Fallback to Gemini (cloud)
        from src.brain.tools_gemini import generate_with_fallback
        return generate_with_fallback(prompt), "Gemini-Cloud"
```

#### Tunnel Lifecycle Management

```bash
# Automatic startup (on app launch)
sshpass -p <passwd> ssh -N \
  -o ControlMaster=auto \
  -o ControlPath=~/.ssh/synth-tunnel-{PID} \
  -L 11434:localhost:11434 \
  -L 11435:localhost:11435 \
  -L 11436:localhost:11436 \
  user@delta.cs.uwindsor.ca

# Automatic cleanup (on app exit / Cmd+Q / kill)
1. pkill -f "ssh.*11434"         # Kill all tunnel processes
2. ssh -O exit <control-socket>  # Clean remote socket
3. os.killpg(pgid, SIGTERM)     # Force cleanup process group
4. rm ~/.ssh/synth-tunnel-{PID}  # Remove socket file
```

### Gemini Integration

**Purpose**: Intelligent fallback when Delta unavailable  
**Models Used**: 
- `gemini-1.5-flash-8b` (primary, free tier)
- `gemini-2.0-flash-exp` (experimental, faster)
- `gemini-1.5-pro` (complex queries, paid)

#### Fallback Strategy

```python
def generate_with_fallback(prompt, max_retries=3):
    """Intelligent model selection + retry"""
    # Try free models first
    for model in GEMINI_FREE_MODELS:
        try:
            response = genai.GenerativeModel(model).generate_content(prompt)
            return response
        except ResourceExhausted:
            continue  # Rate limited, try next
    
    # Fallback to paid model if free exhausted
    return genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt)
```

---

## 🔌 Plugin System

### Architecture

**Plugin Manager**: Dynamic loading of `.py` files from `src/plugins/`  
**Base Class**: `BasePlugin` with metadata and execution hooks  
**Discovery**: Auto-detects plugins on startup

#### Plugin Lifecycle

```python
class PluginManager:
    def load_all_plugins(self):
        """Scan plugins directory"""
        for file in Path("src/plugins").glob("*.py"):
            if file.stem.startswith("_"):
                continue
            plugin = self.load_plugin(file)
            self.plugins[plugin.metadata.name] = plugin
    
    def get_suggestions(self, context: PluginContext):
        """Get relevant plugins for current context"""
        suggestions = []
        for plugin in self.plugins.values():
            if plugin.enabled and plugin.can_handle(context):
                suggestion = plugin.get_suggestion(context)
                suggestions.append(suggestion)
        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)
```

### Available Plugins (14+)

| Plugin | Trigger | Action |
|--------|---------|--------|
| **Weather** | "weather in..." | Fetches wttr.in data |
| **Wikipedia** | Entity names | Opens wiki article |
| **News** | "latest news..." | Searches current events |
| **YouTube** | "youtube..." | Opens video search |
| **Calculator** | Math expressions | Evaluates formula |
| **Dictionary** | "define..." | Looks up word |
| **Translation** | "translate..." | Google Translate |
| **Summarizer** | Long text | Condenses content |
| **Code Explainer** | Code snippets | Analyzes syntax |
| **Email Drafter** | Email context | Generates reply |
| **URL Opener** | Contains URL | Opens in browser |
| **File Finder** | "find file..." | Searches filesystem |
| **Screenshot** | "capture..." | Takes screen grab |
| **Timer** | "remind me..." | Sets notification |

#### Example Plugin Implementation

```python
# src/plugins/weather_plugin.py
class WeatherPlugin(BasePlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="weather",
            version="1.0.0",
            author="Sushant Sharma",
            description="Real-time weather information"
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if this plugin should activate"""
        text = context.clipboard_text.lower()
        return any(word in text for word in ['weather', 'temperature', 'forecast'])
    
    def get_suggestion(self, context: PluginContext) -> PluginSuggestion:
        """Generate actionable suggestion"""
        # Extract location from text
        location = self.extract_location(context.clipboard_text)
        
        return PluginSuggestion(
            plugin_name="weather",
            title=f"Get Weather for {location}",
            description=f"Fetch current weather data",
            confidence=0.9,
            action_type="fetch_data",
            action_params={"location": location}
        )
    
    def execute(self, context: PluginContext) -> str:
        """Fetch and format weather data"""
        location = self.extract_location(context.clipboard_text)
        response = requests.get(f"https://wttr.in/{location}?format=j1")
        data = response.json()
        
        return f"""🌤️ Weather in {location}
Temperature: {data['current_condition'][0]['temp_C']}°C
Condition: {data['current_condition'][0]['weatherDesc'][0]['value']}
Humidity: {data['current_condition'][0]['humidity']}%"""
```

---

## 🗄️ Vector RAG System

### Qdrant Local Database

**Purpose**: Store and retrieve project knowledge  
**Embedding Model**: Google Generative AI embeddings  
**Collection**: `synth_knowledge` with 768-dim vectors

#### RAG Pipeline

```python
class SynthRAG:
    def __init__(self):
        self.client = QdrantClient(path="./qdrant_data")
        self.collection_name = "synth_knowledge"
        
    def add_document(self, text: str, source: str, metadata: dict):
        """Add document to vector store"""
        # Generate embedding
        embedding = self.embed_model.embed_query(text)
        
        # Store in Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=uuid.uuid4().hex,
                vector=embedding,
                payload={
                    "text": text,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                    **metadata
                }
            )]
        )
    
    def query(self, query: str, top_k=5, min_score=0.7):
        """Semantic search with relevance filtering"""
        # Embed query
        query_embedding = self.embed_model.embed_query(query)
        
        # Search Qdrant
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=min_score
        )
        
        return {
            'has_context': len(results) > 0,
            'sources': [
                {'text': r.payload['text'], 'score': r.score, 'source': r.payload['source']}
                for r in results
            ]
        }
```

#### RAG-Augmented Query Flow

```
User Query: "What is FIPS 203?"
    │
    ▼
1. Extract Terms: ["FIPS 203", "cryptography"]
    │
    ▼
2. Query RAG (Local): 
   → Found: 3 relevant docs (score > 0.7)
   → Context: "FIPS 203 is Module-Lattice-Based Key Encapsulation..."
    │
    ▼
3. Web Search (Tavily):
   → Query: "FIPS 203 cryptography standard"
   → Found: 6 web sources
    │
    ▼
4. Synthesize Answer (7B Balanced):
   Prompt = Query + RAG Context + Web Results
    │
    ▼
5. Add to RAG for Future Use
   → Store answer + sources for next time
```

---

## 🚀 Installation & Setup

### Prerequisites

- macOS 11.0+ (Big Sur or later)
- Python 3.10+
- SSH access to HPC cluster (optional, Gemini works standalone)
- Google API key (Gemini)
- Tavily API key (web search)

### Step 1: Clone Repository

```bash
git clone https://github.com/sushantsharma22/Project-Synth.git
cd Project-Synth
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install System Dependencies

```bash
# Install Tesseract OCR
brew install tesseract

# Install sshpass (for automated SSH tunnels)
brew install sshpass
```

### Step 5: Configure Environment Variables

Create `.env` file in project root:

```bash
# HPC Cluster (Optional - Gemini fallback works without this)
SSH_ID=your_username@delta.cs.uwindsor.ca
SSH_PASSWD=your_password

# Google Gemini (Required)
GOOGLE_API_KEY=your_gemini_api_key

# Tavily Web Search (Required for web features)
TAVILY_API_KEY=your_tavily_api_key

# Gemini Configuration
GEMINI_FALLBACK_MODELS=gemini-1.5-flash-8b,gemini-2.0-flash-exp
GEMINI_FREE_TIER_ONLY=true
```

### Step 6: Launch Application

```bash
# Run the native menu bar app
python synth_native.py

# OR use the shell script
chmod +x start_synth_ai.sh
./start_synth_ai.sh
```

---

## 📊 Performance Metrics

### Response Times (Measured)

| Mode | Tool/Task | Avg Time | Max Time |
|------|-----------|----------|----------|
| **Ask** | Live Tools (weather/time) | 1.2s | 3s |
| **Ask** | Web Search | 7.3s | 15s |
| **Ask** | Wikipedia | 2.1s | 5s |
| **Agent** | Simple Task (1-2 tools) | 8.5s | 20s |
| **Agent** | Complex Task (5+ tools) | 35s | 90s |
| **Screen** | OCR + Analysis | 5.2s | 10s |
| **Chat** | With Web Search | 9.1s | 18s |
| **Chat** | Memory-Only | 3.4s | 7s |

### Model Performance (Delta HPC)

| Model | Parameters | Throughput | Use Case |
|-------|------------|------------|----------|
| Qwen 2.5 3B | 3 billion | ~50 tokens/s | Routing, classification |
| Qwen 2.5 7B | 7 billion | ~30 tokens/s | Standard queries |
| Qwen 2.5 14B | 14 billion | ~18 tokens/s | Complex reasoning |

### Resource Usage

- **Memory**: 200-400 MB (idle), 600 MB (processing)
- **CPU**: 5-15% (idle), 30-60% (processing)
- **Network**: 10 KB/s (tunnel keep-alive), 500 KB/s (web search)
- **Storage**: 150 MB (app), 50-200 MB (Qdrant DB)

---

## 🧪 Testing & Quality Assurance

### Test Coverage

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage report
pytest --cov=src tests/

# Test specific module
pytest tests/test_brain.py -v
```

### Code Quality Tools

```bash
# Format with Black
black src/ tests/

# Lint with Flake8
flake8 src/ --max-line-length=100

# Type checking with Pyright
pyright src/
```

### Integration Tests

```python
# tests/test_integration.py
def test_ask_mode_weather():
    """Test Ask mode with weather query"""
    app = SynthMenuBarNative.alloc().init()
    result = app.process_query("What's the weather in Toronto?")
    assert "°C" in result or "°F" in result
    assert len(result) > 50

def test_chat_mode_memory():
    """Test chat conversation memory"""
    chat = ChatManager()
    chat.add_message("user", "My name is Alice")
    chat.add_message("assistant", "Nice to meet you, Alice!")
    chat.add_message("user", "What's my name?")
    context = chat.get_context(last_n=3)
    assert any("Alice" in msg.content for msg in context)
```

---

## 📈 Future Enhancements

### Planned Features

1. **Multi-Language Support**
   - UI localization (Spanish, French, Chinese)
   - Multi-lingual RAG with language detection

2. **Voice Integration**
   - Whisper-based voice input
   - Text-to-speech output

3. **Advanced Automation**
   - Scheduled tasks/reminders
   - Email auto-responses
   - Calendar integration

4. **Enhanced Plugins**
   - Slack integration
   - GitHub operations
   - Notion/Evernote sync

5. **Mobile Companion**
   - iOS app with cloud sync
   - Cross-device conversation history

6. **Performance Optimization**
   - Parallel tool execution
   - Response streaming
   - Caching layer for repeated queries

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests before committing
pytest tests/ -v
```

---

## 📝 License

This project is licensed under the **Apache License 2.0** - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Sushant Sharma**

- Email: ssewuna123@gmail.com
- GitHub: [@sushantsharma22](https://github.com/sushantsharma22)
- LinkedIn: [linkedin.com/in/sushantsharma22](https://linkedin.com/in/sushantsharma22)
- University: University of Windsor (Graduate Student)

### About the Developer

Graduate student specializing in AI/ML Engineering with focus on:
- 🤖 Multi-modal AI systems
- 🧠 Local-cloud hybrid architectures  
- 🔐 Post-quantum cryptography research
- 📊 Production ML deployment

---

## 🙏 Acknowledgments

- **University of Windsor** - For providing HPC cluster access
- **Ollama Team** - For excellent local LLM framework
- **LangChain Community** - For agent orchestration tools
- **Google Gemini** - For powerful cloud AI fallback
- **Tavily** - For high-quality web search API

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/sushantsharma22/Project-Synth/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sushantsharma22/Project-Synth/discussions)
- **Email**: ssewuna123@gmail.com

---

## 📊 Project Statistics

![Lines of Code](https://img.shields.io/badge/Lines%20of%20Code-15%2C000%2B-blue)
![Files](https://img.shields.io/badge/Files-80%2B-green)
![Languages](https://img.shields.io/badge/Languages-Python%20%7C%20Shell-yellow)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)

---

**⭐ Star this repository if you find it useful!**

---

*Last Updated: November 25, 2025*