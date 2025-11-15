"""
🎯 SYNTH MENU BAR APP - SIRI STYLE 🎯
macOS Menu Bar Application with Siri-like Interface

Features:
- Clean text input like Siri
- Smart context detection from screen
- Action buttons on right side
- Natural language processing
- Direct integration with Brain + Plugins

Author: Sushant Sharma
"""

import sys
import rumps
import pyperclip
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QLabel, QListWidget, QListWidgetItem,
                             QPushButton, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from brain_client import DeltaBrain
from src.plugins.plugin_manager import PluginManager
from src.plugins.base_plugin import PluginContext
from src.senses.screen_capture import ScreenCapture


class FloatingPanel(QMainWindow):
    """Siri-like floating panel for natural queries"""
    
    def __init__(self):
        super().__init__()
        self.brain = DeltaBrain()
        self.screen_capture = ScreenCapture()
        self.init_plugins()
        self.init_ui()
        self.detected_context = ""
        
    def init_plugins(self):
        """Initialize plugin system"""
        plugin_dirs = [str(project_root / "src" / "plugins" / "core")]
        self.plugin_manager = PluginManager(plugin_dirs=plugin_dirs)
        self.plugin_manager.load_all_plugins()
        
    def init_ui(self):
        """Setup the Siri-like floating panel UI"""
        # Window settings
        self.setWindowTitle("Synth")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Larger size for Siri-like interface (starts compact)
        self.setGeometry(100, 100, 700, 450)
        self.hide()  # Start hidden, only show when user clicks menu
        
        # Main widget
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 25, 250);
                border-radius: 20px;
            }
        """)
        self.setCentralWidget(main_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Left side - Main input area
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # Siri-like orb/title
        title_container = QHBoxLayout()
        orb_label = QLabel("🧠")
        orb_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 40px;
                background: transparent;
            }
        """)
        title_label = QLabel("Synth")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: 300;
                background: transparent;
            }
        """)
        title_container.addWidget(orb_label)
        title_container.addWidget(title_label)
        title_container.addStretch()
        left_layout.addLayout(title_container)
        
        # Context detection label (shows what Synth sees)
        self.context_label = QLabel("Analyzing screen context...")
        self.context_label.setStyleSheet("""
            QLabel {
                color: rgba(150, 150, 255, 200);
                font-size: 12px;
                background: transparent;
                padding: 5px;
                font-style: italic;
            }
        """)
        self.context_label.setWordWrap(True)
        left_layout.addWidget(self.context_label)
        
        # Main query input (Siri-like)
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("What would you like me to do?")
        self.query_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(40, 40, 50, 180);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-size: 16px;
                font-weight: 300;
            }
            QTextEdit:focus {
                background-color: rgba(50, 50, 60, 200);
            }
        """)
        self.query_input.setMaximumHeight(120)
        left_layout.addWidget(self.query_input)
        
        # Example prompts
        examples_label = QLabel("💡 Try: \"Draft an email about...\" or \"Analyze this code\" or \"What's on screen?\"")
        examples_label.setStyleSheet("""
            QLabel {
                color: rgba(120, 120, 130, 180);
                font-size: 11px;
                background: transparent;
                padding: 5px;
            }
        """)
        examples_label.setWordWrap(True)
        left_layout.addWidget(examples_label)
        
        # Response display
        response_label = QLabel("Response:")
        response_label.setStyleSheet("""
            QLabel {
                color: rgba(180, 180, 200, 200);
                font-size: 12px;
                background: transparent;
                font-weight: bold;
            }
        """)
        left_layout.addWidget(response_label)
        
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 40, 150);
                color: rgba(100, 200, 255, 255);
                border: 1px solid rgba(70, 70, 90, 100);
                border-radius: 10px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        left_layout.addWidget(self.result_display)
        
        # Bottom controls
        bottom_controls = QHBoxLayout()
        
        analyze_btn = QPushButton("✨ Analyze (⏎)")
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(74, 144, 226, 200);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(94, 164, 246, 230);
            }
            QPushButton:pressed {
                background-color: rgba(54, 124, 206, 200);
            }
        """)
        analyze_btn.clicked.connect(self.process_query)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 60, 70, 150);
                color: rgba(200, 200, 210, 200);
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 90, 180);
            }
        """)
        clear_btn.clicked.connect(self.clear_all)
        
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(200, 200, 210, 150);
                border: none;
                padding: 10px 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                color: rgba(255, 100, 100, 200);
            }
        """)
        close_btn.clicked.connect(self.hide)
        
        bottom_controls.addWidget(analyze_btn)
        bottom_controls.addWidget(clear_btn)
        bottom_controls.addStretch()
        bottom_controls.addWidget(close_btn)
        
        left_layout.addLayout(bottom_controls)
        
        # Right side - Quick Actions Panel
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                padding: 5px;
            }
        """)
        right_layout.addWidget(actions_title)
        
        # Action buttons with icons
        self.create_action_button("📧 Draft Email", self.draft_email, right_layout)
        self.create_action_button("📝 Summarize", self.summarize_content, right_layout)
        self.create_action_button("💻 Explain Code", self.explain_code, right_layout)
        self.create_action_button("🔍 Web Search", self.web_search, right_layout)
        self.create_action_button("📅 Add to Calendar", self.add_calendar, right_layout)
        self.create_action_button("🔐 Security Check", self.security_check, right_layout)
        self.create_action_button("📊 Analyze Screen", self.analyze_screen, right_layout)
        self.create_action_button("🎨 Get Creative", self.creative_mode, right_layout)
        
        right_layout.addStretch()
        
        # Add both sides to main layout
        main_layout.addLayout(left_layout, 2)  # Left takes 2/3
        main_layout.addLayout(right_layout, 1)  # Right takes 1/3
        
        main_widget.setLayout(main_layout)
        
        # Auto-detect timer
        self.detect_timer = QTimer()
        self.detect_timer.timeout.connect(self.auto_detect_context)
        self.detect_timer.start(2000)  # Check every 2 seconds
    
    def create_action_button(self, text, callback, layout):
        """Create a styled action button"""
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 60, 150);
                color: white;
                border: 1px solid rgba(80, 80, 100, 100);
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 90, 200);
                border: 1px solid rgba(100, 150, 255, 150);
            }
            QPushButton:pressed {
                background-color: rgba(90, 90, 110, 220);
            }
        """)
        btn.clicked.connect(callback)
        layout.addWidget(btn)
        return btn
    
    def auto_detect_context(self):
        """Auto-detect context from clipboard (optional, not forced)"""
        try:
            # Get clipboard but don't force it into queries
            clipboard_text = pyperclip.paste()
            
            if clipboard_text and len(clipboard_text.strip()) > 3:
                preview = clipboard_text[:80].replace('\n', ' ')
                self.detected_context = clipboard_text
                self.context_label.setText(f"📋 Context available: {preview}...")
            else:
                self.context_label.setText("� Ask me anything or describe what you need...")
                self.detected_context = ""
            
        except Exception as e:
            self.context_label.setText(f"💬 Ready for your request...")
    
    def process_query(self):
        """Process user query with Brain AI"""
        query = self.query_input.toPlainText().strip()
        
        if not query:
            self.result_display.setText("💬 Please type what you'd like me to do...")
            return
        
        # Check if user wants screen analysis
        if any(word in query.lower() for word in ['screen', 'on my screen', 'what do you see', 'analyze screen']):
            # User wants actual screen analysis, not clipboard
            self.result_display.setText("� Capturing screen for analysis...")
            QApplication.processEvents()
            self.analyze_screen()
            return
        
        # Build context only if clipboard seems relevant
        full_context = ""
        if self.detected_context and not query.lower().startswith(('what', 'draft', 'create', 'give me')):
            # Only include clipboard for summarize/explain type queries
            full_context = f"Context from clipboard:\n{self.detected_context[:500]}\n\n"
        
        final_query = full_context + query
        
        self.result_display.setText("🧠 Thinking...")
        QApplication.processEvents()
        
        # Resize window based on expected response
        self.adjust_window_size(len(query))
        
        try:
            # Ask Brain AI
            response = self.brain.ask(final_query, mode="balanced")
            self.result_display.setText(response)
            
            # Expand window to fit response
            self.adjust_window_size(len(response))
            
        except Exception as e:
            self.result_display.setText(f"❌ Error: {str(e)}")
    
    def adjust_window_size(self, content_length):
        """Dynamically adjust window height based on content"""
        base_height = 450
        
        if content_length > 1000:
            new_height = 700
        elif content_length > 500:
            new_height = 600
        elif content_length > 200:
            new_height = 500
        else:
            new_height = base_height
        
        # Smooth resize
        current_geom = self.geometry()
        self.setGeometry(current_geom.x(), current_geom.y(), 700, new_height)
    
    def clear_all(self):
        """Clear all inputs and outputs"""
        self.query_input.clear()
        self.result_display.clear()
        self.detected_context = ""
        self.context_label.setText("👀 Ready for your next request...")
    
    # Quick Action Handlers
    def draft_email(self):
        """Draft an email based on context"""
        context = self.detected_context or "the current situation"
        self.query_input.setText(f"Draft a professional email about: {context}")
        self.process_query()
    
    def summarize_content(self):
        """Summarize clipboard or screen content"""
        if self.detected_context:
            self.query_input.setText("Summarize this in 3-5 bullet points")
            self.process_query()
        else:
            self.result_display.setText("📋 Please copy some text first, then click Summarize")
    
    def explain_code(self):
        """Explain code from clipboard"""
        if self.detected_context:
            self.query_input.setText("Explain this code in simple terms. What does it do?")
            self.process_query()
        else:
            self.result_display.setText("💻 Please copy some code first, then click Explain Code")
    
    def web_search(self):
        """Perform web search"""
        query = self.query_input.toPlainText().strip() or self.detected_context
        if query:
            self.result_display.setText(f"🔍 Searching web for: {query[:100]}...")
            # TODO: Integrate with web_search_plugin
        else:
            self.result_display.setText("🔍 Please type or paste what you want to search for")
    
    def add_calendar(self):
        """Add event to calendar"""
        context = self.detected_context or self.query_input.toPlainText().strip()
        if context:
            self.query_input.setText(f"Create a calendar event from this: {context}")
            self.process_query()
        else:
            self.result_display.setText("📅 Please describe the event you want to add")
    
    def security_check(self):
        """Run security analysis"""
        if self.detected_context:
            self.query_input.setText("Analyze this for security issues, vulnerabilities, or suspicious content")
            self.process_query()
        else:
            self.result_display.setText("🔐 Please copy text/code to analyze for security")
    
    def analyze_screen(self):
        """Capture and analyze current screen with OCR"""
        self.result_display.setText("📸 Taking screenshot in 2 seconds...\n\nGet ready to show what you want analyzed!")
        QApplication.processEvents()
        
        # Give user time to prepare
        import time
        time.sleep(2)
        
        try:
            # Hide this window temporarily so it doesn't appear in screenshot
            self.hide()
            time.sleep(0.5)
            
            # Take screenshot
            screenshot_path = self.screen_capture.capture_region()
            
            # Show window again
            self.show()
            
            if screenshot_path:
                # Perform OCR on the screenshot
                try:
                    import pytesseract
                    from PIL import Image
                    
                    self.result_display.setText("🔍 Analyzing screenshot with OCR...")
                    QApplication.processEvents()
                    
                    # Extract text from image
                    image = Image.open(screenshot_path)
                    extracted_text = pytesseract.image_to_string(image)
                    
                    if extracted_text and len(extracted_text.strip()) > 10:
                        # Ask Brain to analyze what's on screen
                        analysis_query = f"I took a screenshot and extracted this text from it. Please analyze what's on the screen and provide helpful insights:\n\n{extracted_text}"
                        
                        self.result_display.setText("🧠 Brain analyzing screenshot content...")
                        QApplication.processEvents()
                        
                        response = self.brain.ask(analysis_query, mode="balanced")
                        
                        final_result = f"📊 SCREEN ANALYSIS:\n\n{response}\n\n---\n📝 Extracted text preview:\n{extracted_text[:300]}..."
                        self.result_display.setText(final_result)
                        
                        # Expand window for full analysis
                        self.adjust_window_size(len(final_result))
                    else:
                        self.result_display.setText(f"📸 Screenshot saved: {screenshot_path}\n\n⚠️ No text detected. The screen might be mostly graphical or the image quality is low.")
                        
                except ImportError:
                    self.result_display.setText(f"📸 Screenshot saved: {screenshot_path}\n\n⚠️ OCR not available. Install pytesseract to analyze text from screenshots.")
            else:
                self.result_display.setText("❌ Screenshot cancelled")
                
        except Exception as e:
            self.show()  # Make sure window is visible again
            self.result_display.setText(f"❌ Error analyzing screen: {str(e)}")
    
    def creative_mode(self):
        """Creative/brainstorming mode"""
        context = self.query_input.toPlainText().strip() or self.detected_context
        if context:
            self.query_input.setText(f"Give me creative ideas and suggestions for: {context}")
            self.process_query()
        else:
            self.result_display.setText("🎨 Tell me what you want creative ideas for!")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif (event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.process_query()
    
    def show_panel(self):
        """Show panel at cursor position with animation"""
        # Position near top center (like Siri/Spotlight)
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2  # Center horizontally
        y = 80  # Near top
        
        # Reset to compact size when opening
        self.setGeometry(x, y, 700, 450)
        
        self.move(x, y)
        self.show()
        self.raise_()  # Bring to front
        self.activateWindow()  # Make active
        self.query_input.setFocus()
        self.auto_detect_context()  # Check for clipboard context


class SynthMenuBar(rumps.App):
    """macOS Menu Bar Application"""
    
    def __init__(self):
        # Simple icon without emoji to avoid double icon issue
        super().__init__(
            "Synth",  # Simple text title
            quit_button=None
        )
        
        # Menu items
        self.menu = [
            rumps.MenuItem("Open Synth", callback=self.open_panel),
            rumps.separator,
            rumps.MenuItem("Quick Analyze", callback=self.quick_analyze),
            rumps.MenuItem("Screenshot + Analyze", callback=self.screenshot_analyze),
            rumps.separator,
            rumps.MenuItem("About Synth", callback=self.show_about),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        
        # Initialize Qt app for floating panel
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.panel = FloatingPanel()
        
    def open_panel(self, _):
        """Open the floating panel"""
        self.panel.show_panel()
        
    def quick_analyze(self, _):
        """Quick clipboard analysis"""
        clipboard = pyperclip.paste()
        if clipboard:
            self.panel.detected_context = clipboard
            self.panel.query_input.setText("Analyze and explain this")
            self.panel.show_panel()
            self.panel.process_query()
        else:
            rumps.alert("Clipboard Empty", "Copy something first, then try Quick Analyze")
    
    def screenshot_analyze(self, _):
        """Take screenshot and analyze"""
        self.panel.show_panel()
        self.panel.analyze_screen()
        
    def show_about(self, _):
        """Show about dialog"""
        rumps.alert(
            "Synth - AI Assistant",
            "Your intelligent macOS companion\n\n"
            "Version: 2.0.0\n"
            "Author: Sushant Sharma\n\n"
            "Features:\n"
            "• Siri-like natural language interface\n"
            "• AI-powered analysis (Ollama)\n"
            "• 8 intelligent plugins\n"
            "• Smart context detection\n"
            "• OCR & screenshot analysis\n\n"
            "Usage:\n"
            "Click 'Open Synth' or use the menu bar icon\n"
            "Type what you want, or use Quick Actions"
        )
    
    def quit_app(self, _):
        """Quit the application"""
        rumps.quit_application()


def main():
    """Main entry point"""
    print("🚀 Starting Synth Menu Bar App...")
    
    # Create and run menu bar app
    app = SynthMenuBar()
    app.run()


if __name__ == "__main__":
    main()
