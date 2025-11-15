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
                             QPushButton, QTextEdit, QScrollArea, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QAction

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
        # Window settings - stays on top but doesn't auto-close
        self.setWindowTitle("Synth")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
            # Removed Popup flag - it was causing the window to close when clicking inside
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Compact starting size (expands as needed)
        self.setGeometry(100, 100, 680, 400)
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
        
        # Main vertical layout (clean, no sidebars)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 20)
        main_layout.setSpacing(12)
        
        # Top bar with title and menu button
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        # Siri-like orb + title
        orb_label = QLabel("🧠")
        orb_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                background: transparent;
            }
        """)
        title_label = QLabel("Synth")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 300;
                background: transparent;
            }
        """)
        
        top_bar.addWidget(orb_label)
        top_bar.addWidget(title_label)
        top_bar.addStretch()
        
        # Close button (×)
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 150);
                border: none;
                border-radius: 15px;
                padding: 0px 10px;
                font-size: 28px;
                font-weight: 300;
            }
            QPushButton:hover {
                background-color: rgba(255, 60, 60, 200);
                color: white;
            }
        """)
        close_btn.clicked.connect(self.hide)
        top_bar.addWidget(close_btn)
        
        # Three-dot menu button
        self.menu_btn = QPushButton("⋯")
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 60, 70, 150);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 100, 200);
            }
        """)
        self.menu_btn.clicked.connect(self.show_quick_actions_menu)
        top_bar.addWidget(self.menu_btn)
        
        main_layout.addLayout(top_bar)
        
        # Context detection label
        self.context_label = QLabel("� Ask me anything...")
        self.context_label.setStyleSheet("""
            QLabel {
                color: rgba(150, 150, 255, 200);
                font-size: 11px;
                background: transparent;
                padding: 3px;
                font-style: italic;
            }
        """)
        self.context_label.setWordWrap(True)
        main_layout.addWidget(self.context_label)
        
        # Main query input (large, expandable)
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("What would you like me to do?")
        self.query_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(40, 40, 50, 180);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-size: 15px;
                font-weight: 300;
                line-height: 1.4;
            }
            QTextEdit:focus {
                background-color: rgba(50, 50, 60, 200);
            }
        """)
        self.query_input.setMinimumHeight(80)
        self.query_input.setMaximumHeight(150)
        main_layout.addWidget(self.query_input)
        
        # Quick action buttons (bottom of input)
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        
        analyze_btn = QPushButton("✨ Ask")
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(74, 144, 226, 200);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(94, 164, 246, 230);
            }
        """)
        analyze_btn.clicked.connect(self.process_query)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 60, 70, 120);
                color: rgba(200, 200, 210, 200);
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 90, 150);
            }
        """)
        clear_btn.clicked.connect(self.clear_all)
        
        button_row.addWidget(analyze_btn)
        button_row.addWidget(clear_btn)
        button_row.addStretch()
        
        main_layout.addLayout(button_row)
        
        # Separator
        separator = QLabel()
        separator.setStyleSheet("""
            QLabel {
                background-color: rgba(70, 70, 80, 100);
                min-height: 1px;
                max-height: 1px;
            }
        """)
        main_layout.addWidget(separator)
        
        # Response area (expands dynamically)
        response_header = QLabel("Response:")
        response_header.setStyleSheet("""
            QLabel {
                color: rgba(180, 180, 200, 200);
                font-size: 11px;
                background: transparent;
                font-weight: bold;
                padding: 5px 0;
            }
        """)
        main_layout.addWidget(response_header)
        
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 40, 100);
                color: rgba(220, 220, 240, 255);
                border: none;
                border-radius: 10px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        self.result_display.setMinimumHeight(150)
        main_layout.addWidget(self.result_display)
        
        main_widget.setLayout(main_layout)
        
        # Auto-detect timer
        self.detect_timer = QTimer()
        self.detect_timer.timeout.connect(self.auto_detect_context)
        self.detect_timer.start(2000)  # Check every 2 seconds
    
    def show_quick_actions_menu(self):
        """Show popup menu with Quick Actions"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 50, 250);
                color: white;
                border: 1px solid rgba(80, 80, 100, 150);
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 30px 10px 10px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: rgba(74, 144, 226, 200);
            }
        """)
        
        # Add Quick Actions to menu
        actions = [
            ("📧 Draft Email", self.draft_email),
            ("📝 Summarize", self.summarize_content),
            ("💻 Explain Code", self.explain_code),
            ("🔍 Web Search", self.web_search),
            ("📅 Add to Calendar", self.add_calendar),
            ("🔐 Security Check", self.security_check),
            ("📊 Analyze Screen", self.analyze_screen),
            ("🎨 Get Creative", self.creative_mode),
        ]
        
        for text, callback in actions:
            action = QAction(text, self)
            action.triggered.connect(callback)
            menu.addAction(action)
        
        # Show menu below the button
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
    
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
        
        # Check if user wants screen analysis - improved keyword detection
        screen_keywords = ['screen', 'window', 'display', 'going on', 'what do you see', 'analyze screen', 'on my screen', 'see on my']
        if any(keyword in query.lower() for keyword in screen_keywords):
            # User wants actual screen analysis, not clipboard
            self.result_display.setText("📸 Capturing your screen for analysis...\n\nWindow will hide in 2 seconds!")
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
        """Dynamically adjust window height based on content - smooth expansion"""
        base_height = 400  # Compact starting size
        
        # Calculate needed height based on content
        if content_length > 2000:
            new_height = min(800, QApplication.primaryScreen().geometry().height() - 150)
        elif content_length > 1000:
            new_height = 700
        elif content_length > 500:
            new_height = 600
        elif content_length > 200:
            new_height = 500
        else:
            new_height = base_height
        
        # Smooth resize with animation
        current_geom = self.geometry()
        if abs(current_geom.height() - new_height) > 50:  # Only animate significant changes
            self.setGeometry(current_geom.x(), current_geom.y(), 680, new_height)
            
            # Adjust result display height proportionally
            if new_height > 500:
                self.result_display.setMinimumHeight(new_height - 300)
            else:
                self.result_display.setMinimumHeight(150)
    
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
        self.result_display.setText("📸 Taking screenshot in 2 seconds...\n\nGet ready!")
        QApplication.processEvents()
        
        # Give user time to prepare
        import time
        time.sleep(2)
        
        try:
            # Hide this window temporarily
            self.hide()
            time.sleep(0.5)
            
            # Take screenshot - capture() returns PIL Image
            screenshot_img = self.screen_capture.capture()
            
            # Show window again
            self.show()
            
            if screenshot_img:
                # Perform OCR on the screenshot
                try:
                    import pytesseract
                    
                    self.result_display.setText("🔍 Analyzing screenshot with OCR...")
                    QApplication.processEvents()
                    
                    # Extract text from PIL Image directly
                    extracted_text = pytesseract.image_to_string(screenshot_img)
                    
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
                        self.result_display.setText(f"📸 Screenshot captured!\n\n⚠️ No text detected. The screen might be mostly graphical or the image quality is low.")
                        
                except ImportError:
                    self.result_display.setText(f"📸 Screenshot captured!\n\n⚠️ OCR not available. Install pytesseract to analyze text from screenshots.")
            else:
                self.result_display.setText("❌ Screenshot failed")
                
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
    
    # Removed focusOutEvent and check_and_hide - they were causing the window to close unexpectedly
    
    def show_panel(self):
        """Show panel directly under menu bar icon like a dropdown"""
        # Get menu bar position (top of screen)
        screen = QApplication.primaryScreen().geometry()
        
        # Position directly under menu bar (right side where Synth icon is)
        # Menu bar is typically at top-right, so position accordingly
        x = screen.width() - 700  # Right side, with some margin
        y = 30  # Just below menu bar (menu bar is ~25px tall)
        
        # Reset to compact size when opening
        self.setGeometry(x, y, 680, 400)
        self.result_display.setMinimumHeight(150)
        
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.query_input.setFocus()
        self.auto_detect_context()


class SynthMenuBar(rumps.App):
    """macOS Menu Bar Application - Siri-style inline query"""
    
    def __init__(self):
        super().__init__("Synth", quit_button=None)
        
        # Initialize AI components
        self.brain = DeltaBrain()
        self.screen_capture = ScreenCapture()
        
        # Simple menu - just the input option
        self.menu = [
            rumps.MenuItem("Ask Synth...", callback=self.ask_inline, key="s")
        ]
    
    def ask_inline(self, _=None):
        """Show inline text input window - Siri style"""
        # Create simple dialog window
        window = rumps.Window(
            message="What would you like to know?",
            title="Synth",
            default_text="",
            ok="Ask",
            cancel="Cancel",
            dimensions=(320, 24)
        )
        
        response = window.run()
        
        if response.clicked:
            query = response.text.strip()
            
            if query:
                # Check if asking about screen
                screen_keywords = ['screen', 'window', 'display', 'going on', 'see on', 'looking at']
                
                if any(keyword in query.lower() for keyword in screen_keywords):
                    # Analyze screen
                    self.analyze_screen_now(query)
                else:
                    # Regular query
                    self.process_quick_query(query)
    
    def process_quick_query(self, query):
        """Process quick query and show result"""
        # Show thinking notification
        rumps.notification("Synth", "Processing...", "🧠 Thinking...")
        
        try:
            # Get response from Brain
            result = self.brain.ask(query, mode="fast")
            
            # Show result in notification
            rumps.notification("Synth", "Answer", result[:200] + "..." if len(result) > 200 else result)
            
        except Exception as e:
            rumps.notification("Synth", "Error", str(e))
    
    def analyze_screen_now(self, original_query):
        """Capture and analyze current screen"""
        # Notify user
        rumps.notification("Synth", "Screen Capture", "Taking screenshot in 2 seconds...")
        
        import time
        time.sleep(2)
        
        try:
            # Capture screen
            screenshot_img = self.screen_capture.capture()
            
            if screenshot_img:
                # Try OCR
                try:
                    import pytesseract
                    
                    rumps.notification("Synth", "Analyzing...", "🔍 Reading screen content...")
                    
                    # Extract text
                    extracted_text = pytesseract.image_to_string(screenshot_img)
                    
                    if extracted_text and len(extracted_text.strip()) > 10:
                        # Build query with screen context
                        full_query = f"Based on this screen content, {original_query}\n\nScreen text:\n{extracted_text[:800]}"
                        
                        # Get analysis
                        result = self.brain.ask(full_query, mode="balanced")
                        
                        # Show result
                        rumps.notification("Synth", "Screen Analysis", result[:200] + "..." if len(result) > 200 else result)
                        
                    else:
                        rumps.notification("Synth", "Screen Capture", "⚠️ No text detected on screen")
                        
                except ImportError:
                    rumps.notification("Synth", "Error", "OCR not available. Install pytesseract.")
            else:
                rumps.notification("Synth", "Error", "Screenshot failed")
                
        except Exception as e:
            rumps.notification("Synth", "Error", str(e))


def main():
    """Main entry point"""
    print("🚀 Starting Synth Menu Bar App...")
    
    # Create and run menu bar app
    app = SynthMenuBar()
    app.run()


if __name__ == "__main__":
    main()
