# Project Synth: Development Roadmap

**Proactive AI Assistant for macOS**

---

## 🎯 Vision

An intelligent, proactive AI assistant that monitors your work, understands context, and offers helpful suggestions - running entirely on your infrastructure for $0 cost.

**Architecture:** Hybrid Client-Server (MacBook M3 + Delta HPC GPU Server)  
**Timeline:** 10-12 weeks  
**Cost:** $0 (100% free stack)

---

## 📍 Current Status: Phase 0 Complete ✅

- ✅ Delta Brain running (3 GPU models on Ollama)
- ✅ SSH tunnel connection established
- ✅ Python client library working
- ✅ Local environment configured

**Next:** Phase 1 - Building the Senses (Detection System)

---

## 🗺️ Complete Roadmap

### **Phase 0: Infrastructure Setup** ✅ COMPLETE (Week 1)

**Objectives:** Set up development environment and persistent server connectivity

**Completed:**
- ✅ Python 3.13 + virtual environment
- ✅ Delta server with Ollama running 24/7
- ✅ LLaVA + Qwen2.5 models deployed (3B, 7B, 14B)
- ✅ SSH tunnel configuration
- ✅ Brain client library (`brain_client.py`)
- ✅ Version control ready

**Deliverables:**
- ✅ Ollama running on Delta HPC
- ✅ Encrypted tunnel to localhost
- ✅ Test suite working
- ✅ Documentation complete

---

### **Phase 1: Senses - Detection System** 🔄 CURRENT (Week 2)

**Objectives:** Build proactive sensing for clipboard and screen monitoring

**Tasks:**

**Days 1-2: Clipboard Monitoring**
- [ ] Implement NSPasteboard clipboard watcher
- [ ] Event-driven callback system
- [ ] Detection delay <500ms
- [ ] Test with various content types

**Days 3-4: Screen Capture**
- [ ] Screenshot capture using `mss` library
- [ ] Image compression/optimization
- [ ] Request macOS Screen Recording permissions
- [ ] Test capture speed (<100KB target)

**Days 5-6: Integrated Trigger System**
- [ ] Combine clipboard + screenshot context
- [ ] Content filtering (skip passwords/tokens)
- [ ] Base64 encoding for transmission
- [ ] Trigger pipeline: detection → context → Brain

**Day 7: Testing & Optimization**
- [ ] Stress test rapid clipboard changes
- [ ] Memory usage monitoring
- [ ] Privacy filter validation
- [ ] Performance metrics documentation

**Deliverables:**
- ⏳ Clipboard detected within 500ms
- ⏳ Screenshots <100KB compressed
- ⏳ Privacy filters active
- ⏳ Context package format defined

---

### **Phase 2: Brain - AI Reasoning** 🔜 (Week 3)

**Objectives:** Connect sensing to AI and create LinkedIn demo

**Tasks:**

**Days 1-2: Ollama API Integration**
- [ ] Enhanced API client for multimodal prompts
- [ ] Text + image prompt construction
- [ ] Timeout handling and error recovery
- [ ] JSON response parsing

**Days 3-4: Prompt Engineering**
- [ ] System prompt for proactive behavior
- [ ] Define action output format
- [ ] Few-shot examples
- [ ] Test reasoning quality

**Days 5-6: LinkedIn Demo**
- [ ] End-to-end KeyError detection scenario
- [ ] Senses → Brain → Suggestion pipeline
- [ ] Mock VS Code screenshot
- [ ] Response time <3 seconds

**Day 7: Validation**
- [ ] Test 10+ scenarios
- [ ] Measure action suggestion accuracy
- [ ] JSON parsing reliability >95%
- [ ] Record demo video

**Deliverables:**
- ⏳ AI reasoning pipeline working
- ⏳ LinkedIn demo functional
- ⏳ Response time <3 seconds
- ⏳ Demo video ready

---

### **Phase 3: Hands - Automation** (Weeks 4-5)

**Objectives:** Build execution capabilities and menu bar UI

**Tasks:**

**Days 1-3: Automation Tools**
- [ ] AppleScript executor
- [ ] Project file search (ripgrep/grep)
- [ ] Clipboard writer
- [ ] macOS notification system
- [ ] Test each tool independently

**Days 4-6: Menu Bar Application**
- [ ] `rumps`-based menu bar UI
- [ ] Status indicator + pause/resume
- [ ] Settings panel
- [ ] Notification → action confirmation
- [ ] App icon design

**Days 7-8: Integration**
- [ ] Brain output → automation execution
- [ ] User confirmation flow
- [ ] Action history/logging
- [ ] Error handling

**Days 9-10: End-to-End Testing**
- [ ] Complete workflow testing
- [ ] UI responsiveness during inference
- [ ] Notification timing
- [ ] Multi-macOS version testing

**Deliverables:**
- ⏳ All automation tools working
- ⏳ Functional menu bar app
- ⏳ Notifications within 3 seconds
- ⏳ Execution success >90%

---

### **Phase 4: Optimization & Polish** (Weeks 6-7)

**Objectives:** Performance, configuration, user experience

**Tasks:**

**Days 1-2: Fast Pre-Filtering**
- [ ] Add Llama 3.2 1B for quick assessment
- [ ] Two-tier reasoning (fast → full)
- [ ] Reduce LLaVA calls by 70%
- [ ] Battery life optimization

**Days 3-4: Configuration System**
- [ ] Settings file (JSON/YAML)
- [ ] App whitelist/blacklist
- [ ] Sensitivity controls
- [ ] Custom keyboard shortcuts

**Days 5-6: Onboarding**
- [ ] First-run wizard
- [ ] Permission explanations
- [ ] User tutorial
- [ ] Helpful tooltips

**Days 7-9: Error Handling**
- [ ] Comprehensive error catching
- [ ] Detailed logging system
- [ ] Debug mode
- [ ] Local crash reporting

**Days 10-11: Performance**
- [ ] Memory footprint reduction
- [ ] Battery mode detection
- [ ] Context caching
- [ ] Performance dashboard

**Days 12-14: User Testing**
- [ ] Recruit 3-5 beta testers
- [ ] Gather usability feedback
- [ ] Fix pain points
- [ ] Iterate based on input

**Deliverables:**
- ⏳ 70% reduction in inference calls
- ⏳ Comprehensive configuration
- ⏳ Smooth onboarding
- ⏳ Production-ready stability

---

### **Phase 5: Advanced Features** (Weeks 8-10)

**Objectives:** Extensibility and advanced capabilities

**Tasks:**

**Days 1-5: MCP Architecture**
- [ ] Model Context Protocol server
- [ ] Modular tool system
- [ ] Plugin loader
- [ ] Plugin API documentation

**Days 6-10: Context-Aware Features**
- [ ] Git integration (commit messages)
- [ ] Security warnings (API key detection)
- [ ] Email/message draft assistance
- [ ] Code documentation helpers

**Days 11-15: Learning System**
- [ ] Track user acceptance/rejection
- [ ] SQLite action history
- [ ] Preference learning
- [ ] Feedback mechanism

**Days 16-20: Advanced Automation**
- [ ] Multi-step workflows
- [ ] Conditional action chains
- [ ] Macro recording
- [ ] Schedule-based actions

**Deliverables:**
- ⏳ Modular plugin system
- ⏳ 5+ context-aware scenarios
- ⏳ User preference learning
- ⏳ Extensible architecture

---

### **Phase 6: Packaging & Distribution** (Weeks 11-12)

**Objectives:** Public release and open-source launch

**Tasks:**

**Days 1-3: Application Packaging**
- [ ] py2app macOS .app bundle
- [ ] Auto-installer for Ollama
- [ ] Model download on first run
- [ ] Test on clean macOS

**Days 4-5: Documentation**
- [ ] Comprehensive README
- [ ] Installation guide
- [ ] Configuration docs
- [ ] Troubleshooting FAQ
- [ ] Tutorial videos

**Days 6-7: Open Source**
- [ ] Choose license (MIT/Apache 2.0)
- [ ] Code cleanup + comments
- [ ] CONTRIBUTING.md
- [ ] GitHub templates

**Days 8-9: Distribution**
- [ ] GitHub repository
- [ ] GitHub Releases setup
- [ ] v1.0 release notes
- [ ] Homebrew Cask (optional)
- [ ] Auto-update checking

**Days 10-12: Launch Prep**
- [ ] Project website/landing page
- [ ] Announcement blog post
- [ ] LinkedIn demo video
- [ ] Technical walkthrough
- [ ] Social media strategy

**Days 13-14: Launch**
- [ ] Release v1.0 on GitHub
- [ ] Post to communities
- [ ] Monitor feedback
- [ ] Rapid support

**Deliverables:**
- ⏳ Installable .app bundle
- ⏳ Complete documentation
- ⏳ Open-source repository live
- ⏳ v1.0 released
- ⏳ Community support established

---

## 🎯 Key Milestones

| Week | Milestone | Success Criteria |
|------|-----------|------------------|
| **1** | ✅ Infrastructure Ready | Server running, tunnel working, <200ms latency |
| **2** | Proactive Detection | Clipboard + screen capture functioning |
| **3** | LinkedIn Demo | End-to-end scenario <3 seconds |
| **5** | Full Automation | Tools working, menu bar app functional |
| **7** | Production Ready | Optimized, tested, stable v1.0 |
| **10** | Feature Complete | Plugin system, learning, advanced features |
| **12** | Public Launch | v1.0 released, docs complete |

---

## 📊 Success Metrics

### Technical
- ⏱️ **Response time:** <3 seconds (trigger → notification)
- ⚡ **Uptime:** >99% (server availability)
- 🎯 **Accuracy:** >80% (suggestions accepted)
- 🔋 **Battery impact:** <5% additional drain

### User Experience
- 🚀 **Installation:** <10 minutes
- ⏰ **Time saved:** >15 min/day
- ⭐ **Satisfaction:** >4/5 stars

### Community
- ⭐ **GitHub stars:** 100+ (Month 1)
- 👥 **Contributors:** 5+ (3 months)
- 🔌 **Plugins:** 10+ (6 months)

---

## ⚠️ Risk Management

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Server morning reboot | High | systemd auto-restart ✅ |
| Model hallucinations | Medium | User confirmation before actions |
| macOS permission denials | Medium | Clear onboarding wizard |
| Network latency | Low | Optimize payload size |
| Battery drain | Low | Fast pre-filtering, battery mode |

---

## 🚀 Post-Launch Roadmap (Weeks 13+)

### Short-term (Months 1-3)
- Bug fixes from user reports
- Performance improvements
- Additional automation scenarios
- Windows/Linux compatibility research

### Medium-term (Months 4-6)
- Multi-language support
- Voice integration option
- Mobile companion app (iPhone)
- Cloud sync for preferences

### Long-term (Months 7-12)
- Fine-tuned custom model
- Enterprise features (team sharing)
- Integration marketplace
- AI model marketplace

---

## 📁 Repository Structure

```
project-synth/
├── src/
│   ├── senses/          # Phase 1: Detection
│   ├── brain/           # Phase 2: AI Reasoning
│   ├── hands/           # Phase 3: Automation
│   └── ui/              # Menu bar app
├── brain_client/        # Delta Brain connection ✅
├── tests/
├── docs/
├── examples/
└── config/
```

---

## 📞 Contact

**Author:** Sushant Sharma  
**Email:** ssewuna123@gmail.com  
**Server:** Delta HPC - University of Windsor

---

**Version:** Phase 0 Complete  
**Last Updated:** November 14, 2025
