# Project Synth: Development Roadmap

**Total Timeline:** 10-12 weeks  
**Architecture:** Hybrid Client-Server (MacBook M3 + University GPU Server)  
**Cost:** $0 (100% free stack)  
**Status:** Phase 0 Complete ✅ | Phase 1 In Progress 🚧

---

## Phase 0: Infrastructure Setup ✅ COMPLETE

**Timeline:** Week 1 (Nov 11-17, 2025)  
**Status:** ✅ DONE

### Objectives
Set up development environment and establish persistent server connectivity

### Completed Tasks
- ✅ Local environment with Python 3.13, venv, dependencies
- ✅ Project directory structure created
- ✅ Git version control initialized
- ✅ Ollama running on Delta HPC (3 models: 3B, 7B, 14B)
- ✅ SSH key-based authentication (ed25519)
- ✅ Persistent SSH tunnel using macOS LaunchAgent
- ✅ Auto-reconnect after disconnections
- ✅ Server connection validated (<200ms latency)
- ✅ All three models tested and verified working
- ✅ Documentation created (SETUP_DOCUMENTATION.md, QUICK_START.md)
- ✅ GitHub repository live at https://github.com/sushantsharma22/Project-Synth.git

### Deliverables
- ✅ Ollama running 24/7 on Delta server
- ✅ Encrypted tunnel auto-connecting on MacBook startup
- ✅ Test suite confirming all infrastructure working
- ✅ Documented setup procedures

### Performance Metrics
- **Connection Latency:** <200ms ✅
- **Tunnel Uptime:** 100% (auto-reconnect working)
- **Model Response Times:**
  - 3B: ~0.7s ✅
  - 7B: ~12-16s ✅
  - 14B: ~18-25s (estimated)

---

## Phase 1: Senses - Detection System 🚧 IN PROGRESS

**Timeline:** Week 2 (Nov 18-24, 2025)  
**Status:** 🚧 STARTING NOW

### Objectives
Build proactive sensing capabilities for clipboard and screen monitoring

### Tasks

#### Days 1-2: Clipboard Monitoring
- [ ] Implement event-driven clipboard watcher using `NSPasteboard`
- [ ] Create callback system for clipboard changes
- [ ] Add detection delay measurement (<500ms target)
- [ ] Test reliability with various content types (text, code, URLs)
- [ ] Add privacy filters (skip passwords, tokens)

**Files to create:**
- `src/senses/clipboard_monitor.py`
- `tests/test_clipboard.py`

#### Days 3-4: Screen Capture
- [ ] Implement screenshot capture using `mss` library
- [ ] Add image compression and optimization (<100KB target)
- [ ] Request macOS Screen Recording permissions
- [ ] Test capture speed and file sizes
- [ ] Add region selection (active window vs full screen)

**Files to create:**
- `src/senses/screen_capture.py`
- `tests/test_screen_capture.py`

#### Days 5-6: Integrated Trigger System
- [ ] Combine clipboard + screenshot into context package
- [ ] Implement content filtering (skip sensitive data)
- [ ] Create base64 encoding for network transmission
- [ ] Build trigger pipeline: detection → context creation
- [ ] Add configurable trigger conditions

**Files to create:**
- `src/senses/trigger_system.py`
- `src/senses/context_builder.py`

#### Day 7: Testing & Optimization
- [ ] Stress test with rapid clipboard changes
- [ ] Measure memory usage during extended operation
- [ ] Verify no sensitive data leaks
- [ ] Document performance metrics
- [ ] Create demo scenarios

### Deliverables
- [ ] Clipboard changes detected within 500ms
- [ ] Screenshots compressed to <100KB
- [ ] Privacy filters preventing sensitive data capture
- [ ] Complete context package format defined

### Success Criteria
- Detection speed: <500ms from clipboard change to trigger
- Image size: <100KB per screenshot
- Memory usage: <50MB for monitoring process
- Privacy: 100% blocking of passwords, API keys, tokens

---

## Phase 2: Brain - AI Reasoning

**Timeline:** Week 3 (Nov 25-Dec 1, 2025)  
**Status:** ⏳ PENDING

### Objectives
Connect sensing to AI reasoning and create the flagship demo

### Tasks

#### Days 1-2: Ollama API Integration
- [ ] Build API client for remote Ollama calls
- [ ] Implement multimodal prompt construction (text + image)
- [ ] Add timeout handling and error recovery
- [ ] Test response parsing and JSON extraction

**Files to create:**
- `src/brain/ollama_client.py` (enhance existing brain_client.py)
- `src/brain/prompt_builder.py`

#### Days 3-4: Prompt Engineering
- [ ] Design system prompt for proactive agent behavior
- [ ] Define available actions and output format
- [ ] Create examples for few-shot learning
- [ ] Test reasoning quality with various scenarios

**Files to create:**
- `src/brain/prompts.py`
- `src/brain/action_definitions.py`

#### Days 5-6: LinkedIn Demo Creation
- [ ] Build end-to-end KeyError detection scenario
- [ ] Integrate senses → brain → suggestion pipeline
- [ ] Create mock VS Code screenshot for testing
- [ ] Measure total response time (target: <3 seconds)

**Files to create:**
- `examples/linkedin_demo.py`
- `examples/mock_scenarios/`

#### Day 7: Validation
- [ ] Test with 10+ different scenarios (errors, URLs, code snippets)
- [ ] Measure accuracy of action suggestions
- [ ] Verify JSON parsing reliability (>95% target)
- [ ] Record demo video for showcase

### Deliverables
- [ ] Working AI reasoning pipeline
- [ ] LinkedIn demo functioning end-to-end
- [ ] Response time under 3 seconds
- [ ] Demo video ready to share

### Success Criteria
- Response time: <3 seconds (trigger to notification)
- Accuracy: >80% (suggestions are helpful)
- Reliability: >95% (JSON parsing success)

---

## Phase 3: Hands - Automation

**Timeline:** Weeks 4-5 (Dec 2-15, 2025)  
**Status:** ⏳ PENDING

### Objectives
Build execution capabilities and user interface

### Tasks

#### Days 1-3: Automation Tools
- [ ] Implement AppleScript executor for app control
- [ ] Create project file search using ripgrep/grep
- [ ] Build clipboard writer functionality
- [ ] Add macOS notification system
- [ ] Test each tool independently

**Files to create:**
- `src/hands/applescript_executor.py`
- `src/hands/file_search.py`
- `src/hands/clipboard_writer.py`
- `src/hands/notification_manager.py`

#### Days 4-6: Menu Bar Application
- [ ] Create rumps-based menu bar UI
- [ ] Add status indicator and pause/resume controls
- [ ] Implement settings panel for configuration
- [ ] Build notification → action confirmation flow
- [ ] Design and create app icon

**Files to create:**
- `src/ui/menu_bar.py`
- `src/ui/settings_panel.py`
- `assets/icon.icns`

#### Days 7-8: Integration
- [ ] Connect brain output to hands execution
- [ ] Add user confirmation before executing actions
- [ ] Implement action history/logging
- [ ] Handle execution errors gracefully

**Files to create:**
- `src/core/action_executor.py`
- `src/core/confirmation_dialog.py`

#### Days 9-10: End-to-End Testing
- [ ] Test complete workflow from clipboard → execution
- [ ] Verify UI remains responsive during inference
- [ ] Check notification timing and reliability
- [ ] Test on multiple macOS versions if possible

### Deliverables
- [ ] All automation tools working reliably
- [ ] Functional menu bar application
- [ ] Notifications appear within 3 seconds of trigger
- [ ] Action execution success rate >90%

---

## Phase 4: Optimization & Polish

**Timeline:** Weeks 6-7 (Dec 16-29, 2025)  
**Status:** ⏳ PENDING

### Objectives
Improve performance, add configuration, enhance user experience

### Tasks

#### Days 1-2: Fast Pre-Filtering
- [ ] Add lightweight Llama 3.2 1B for quick content assessment
- [ ] Implement two-tier reasoning (fast filter → full analysis)
- [ ] Reduce unnecessary LLaVA calls by 70%+
- [ ] Measure battery life improvement

#### Days 3-4: Configuration System
- [ ] Create settings file (JSON/YAML format)
- [ ] Add application whitelist/blacklist
- [ ] Implement sensitivity adjustment controls
- [ ] Add custom keyboard shortcuts option

#### Days 5-6: Onboarding Experience
- [ ] Build first-run wizard for permissions
- [ ] Create clear explanations for each permission request
- [ ] Add tutorial for first-time users
- [ ] Design helpful tooltips and documentation

#### Days 7-9: Error Handling & Logging
- [ ] Implement comprehensive error catching
- [ ] Add detailed logging system
- [ ] Create debug mode for troubleshooting
- [ ] Build automatic crash reporting (local only)

#### Days 10-11: Performance Optimization
- [ ] Reduce memory footprint
- [ ] Optimize battery usage (detect battery mode)
- [ ] Implement context caching to reduce redundant captures
- [ ] Add performance monitoring dashboard

#### Days 12-14: User Testing
- [ ] Recruit 3-5 beta testers
- [ ] Gather feedback on usability
- [ ] Identify and fix top pain points
- [ ] Iterate based on user input

### Deliverables
- [ ] Fast filter reducing inference calls by 70%
- [ ] Comprehensive configuration options
- [ ] Smooth onboarding experience
- [ ] Stable, production-ready application

---

## Phase 5: Advanced Features

**Timeline:** Weeks 8-10 (Dec 30, 2025 - Jan 19, 2026)  
**Status:** ⏳ PENDING

### Tasks

#### MCP Architecture (Days 1-5)
- [ ] Design Model Context Protocol server structure
- [ ] Create modular tool system
- [ ] Build plugin loader for community tools
- [ ] Document plugin API

#### Context-Aware Features (Days 6-10)
- [ ] Add Git integration (commit message suggestions)
- [ ] Implement security warnings (API key detection)
- [ ] Build email/message draft assistance
- [ ] Create code documentation helpers

#### Learning System (Days 11-15)
- [ ] Track which suggestions users accept/ignore
- [ ] Store action history in local SQLite database
- [ ] Implement basic preference learning
- [ ] Add feedback mechanism for incorrect suggestions

#### Advanced Automation (Days 16-20)
- [ ] Add multi-step workflow support
- [ ] Implement conditional action chains
- [ ] Create macro recording capability
- [ ] Build schedule-based actions

### Deliverables
- [ ] Modular plugin system
- [ ] 5+ context-aware automation scenarios
- [ ] User preference learning functional
- [ ] Extensible architecture for community contributions

---

## Phase 6: Packaging & Distribution

**Timeline:** Weeks 11-12 (Jan 20 - Feb 2, 2026)  
**Status:** ⏳ PENDING

### Tasks

#### Application Packaging (Days 1-3)
- [ ] Use py2app to create macOS .app bundle
- [ ] Include auto-installer for Ollama
- [ ] Add model download on first run
- [ ] Test installation on clean macOS systems

#### Documentation (Days 4-5)
- [ ] Write comprehensive README
- [ ] Create installation guide
- [ ] Document all configuration options
- [ ] Build troubleshooting FAQ
- [ ] Record tutorial videos

#### Open Source Preparation (Days 6-7)
- [ ] Choose license (MIT or Apache 2.0 recommended)
- [ ] Clean up code and add comments
- [ ] Create CONTRIBUTING.md for community
- [ ] Set up GitHub Issues and pull request templates

#### Distribution Setup (Days 8-9)
- [ ] Enhance GitHub repository
- [ ] Set up GitHub Releases
- [ ] Write release notes for v1.0
- [ ] Create Homebrew Cask formula (optional)
- [ ] Set up automatic update checking

#### Launch Preparation (Days 10-12)
- [ ] Create project website/landing page
- [ ] Write announcement blog post
- [ ] Prepare LinkedIn demo video
- [ ] Record technical deep-dive walkthrough
- [ ] Plan social media promotion strategy

#### Launch & Support (Days 13-14)
- [ ] Release v1.0 on GitHub
- [ ] Post to relevant communities (Reddit, Hacker News)
- [ ] Monitor feedback and issues
- [ ] Provide rapid support for early adopters

### Deliverables
- [ ] Installable .app bundle
- [ ] Complete documentation
- [ ] Open-source repository enhanced
- [ ] v1.0 released publicly
- [ ] Community support channels established

---

## Key Milestones

| Week | Milestone | Success Criteria | Status |
|------|-----------|------------------|--------|
| 1 | Infrastructure Ready | Server running, tunnel working, <200ms latency | ✅ COMPLETE |
| 2 | Proactive Detection | Clipboard + screen capture functioning | 🚧 IN PROGRESS |
| 3 | LinkedIn Demo | End-to-end scenario working in <3 seconds | ⏳ PENDING |
| 5 | Full Automation | All tools working, menu bar app functional | ⏳ PENDING |
| 7 | Production Ready | Optimized, tested, stable v1.0 candidate | ⏳ PENDING |
| 10 | Feature Complete | Plugin system, learning, advanced features | ⏳ PENDING |
| 12 | Public Launch | v1.0 released, documentation complete | ⏳ PENDING |

---

## Resource Requirements

### Developer Time
- **Full-time:** 10-12 weeks
- **Part-time (20 hrs/week):** 20-24 weeks

### Hardware
- ✅ MacBook Air M3 (you have this)
- ✅ University server access with 4 GPUs (you have this)
- ✅ No additional hardware needed

### Software/Services
- ✅ All free and open-source
- ✅ $0 total cost

---

## Risk Management

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Server morning reboot | High | systemd auto-restart | ✅ Implemented |
| Model hallucinations | Medium | User confirmation before actions | ⏳ Phase 3 |
| macOS permission denials | Medium | Clear onboarding wizard | ⏳ Phase 4 |
| Network latency issues | Low | Test from multiple locations, optimize payload size | ⏳ Phase 2 |
| Battery drain | Low | Fast pre-filtering, battery mode detection | ⏳ Phase 4 |

---

## Success Metrics

### Technical
- **Response time:** <3 seconds (trigger to notification)
- **Uptime:** >99% (server availability) - ✅ Currently 100%
- **Accuracy:** >80% (action suggestions accepted by user)
- **Battery impact:** <5% additional drain

### User Experience
- **Installation time:** <10 minutes
- **Time saved per day:** >15 minutes for target users
- **User satisfaction:** >4/5 stars in feedback

### Community
- **GitHub stars:** 100+ in first month
- **Contributors:** 5+ within 3 months
- **Plugin ecosystem:** 10+ community tools within 6 months

---

## Post-Launch Roadmap (Weeks 13+)

### Short-term (Months 1-3)
- Bug fixes based on user reports
- Performance improvements
- Additional automation scenarios
- Windows/Linux compatibility research

### Medium-term (Months 4-6)
- Multi-language support
- Voice integration option
- Mobile companion app (view suggestions on iPhone)
- Cloud sync for preferences (optional)

### Long-term (Months 7-12)
- Fine-tuned custom model for specific workflows
- Enterprise features (team sharing, admin controls)
- Integration marketplace
- AI model marketplace (let users choose LLaVA vs others)

---

**Last Updated:** November 14, 2025  
**Current Phase:** Phase 1 - Senses (Week 2)  
**Next Milestone:** Proactive Detection Complete (Nov 24, 2025)
