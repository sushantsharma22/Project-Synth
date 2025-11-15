"""
🎯 SYNTH MENU BAR APP 🎯
macOS Menu Bar Application with Transparent Dropdown

Features:
- Icon in menu bar (near WiFi)
- Transparent floating panel on click
- Auto-detect clipboard/selected text
- Query input with smart suggestions
- Direct integration with Brain + Plugins

Author: Sushant Sharma
"""

import sys
import rumps
import pyperclip
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QLabel, QListWidget, QListWidgetItem,
                             QPushButton, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from brain_client import DeltaBrain
from src.plugins.plugin_manager import PluginManager
from src.plugins.base_plugin import PluginContext
from src.senses.screen_capture import ScreenCapture


class FloatingPanel(QMainWindow):
    """Transparent floating panel for queries"""
    
    def __init__(self):
        super().__init__()
        self.brain = DeltaBrain()
        self.init_plugins()
        self.init_ui()
        
    def init_plugins(self):
        """Initialize plugin system"""
        plugin_dirs = [str(project_root / "src" / "plugins" / "core")]
        self.plugin_manager = PluginManager(plugin_dirs=plugin_dirs)
        self.plugin_manager.load_all_plugins()
        
    def init_ui(self):
        """Setup the floating panel UI"""
        # Window settings
        self.setWindowTitle("Synth Assistant")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Size and position
        self.setGeometry(100, 100, 500, 400)
        
        # Main widget
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 240);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        self.setCentralWidget(main_widget)
        
        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🧠 Synth Assistant")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                padding: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Context label (shows what's detected)
        self.context_label = QLabel("📋 Auto-detecting context...")
        self.context_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
                background: transparent;
                padding: 5px;
            }
        """)
        layout.addWidget(self.context_label)
        
        # Query input
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Ask anything or press Enter to analyze...")
        self.query_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(50, 50, 50, 200);
                color: white;
                border: 2px solid #555;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4a9eff;
            }
        """)
        self.query_input.returnPressed.connect(self.process_query)
        layout.addWidget(self.query_input)
        
        # Quick actions
        actions_label = QLabel("💡 Quick Actions:")
        actions_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 11px;
                background: transparent;
                padding: 3px;
            }
        """)
        layout.addWidget(actions_label)
        
        # Suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(40, 40, 40, 200);
                color: white;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: rgba(70, 70, 70, 200);
            }
            QListWidget::item:selected {
                background-color: rgba(74, 158, 255, 150);
            }
        """)
        self.suggestions_list.itemDoubleClicked.connect(self.execute_suggestion)
        layout.addWidget(self.suggestions_list)
        
        # Result display
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setMaximumHeight(100)
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(40, 40, 40, 200);
                color: #4a9eff;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.result_display)
        
        # Close button
        close_btn = QPushButton("✕ Close (Esc)")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 200);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 200);
            }
        """)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)
        
        main_widget.setLayout(layout)
        
        # Auto-detect timer
        self.detect_timer = QTimer()
        self.detect_timer.timeout.connect(self.auto_detect)
        self.detect_timer.start(1000)  # Check every second
        
    def auto_detect(self):
        """Auto-detect clipboard and provide suggestions"""
        try:
            clipboard_text = pyperclip.paste()
            
            if not clipboard_text or len(clipboard_text.strip()) < 3:
                self.context_label.setText("📋 Clipboard empty - Copy something to analyze")
                return
            
            # Show what's detected
            preview = clipboard_text[:60].replace('\n', ' ')
            self.context_label.setText(f"📋 Detected: {preview}...")
            
            # Get plugin suggestions
            context = PluginContext(clipboard_text=clipboard_text)
            suggestions = self.plugin_manager.get_suggestions(context)
            
            # Update suggestions list
            self.suggestions_list.clear()
            for sug in suggestions[:8]:  # Top 8 suggestions
                item = QListWidgetItem(f"{sug.title} ({sug.confidence:.0%})")
                item.setData(Qt.ItemDataRole.UserRole, sug)
                self.suggestions_list.addItem(item)
            
        except Exception as e:
            self.context_label.setText(f"⚠️ Error: {str(e)[:50]}")
    
    def process_query(self):
        """Process user query with Brain"""
        query = self.query_input.text().strip()
        
        if not query:
            # No query - just analyze clipboard
            clipboard_text = pyperclip.paste()
            if clipboard_text:
                query = f"Analyze this and suggest next steps:\n\n{clipboard_text[:500]}"
            else:
                self.result_display.setText("❌ Nothing to analyze")
                return
        
        self.result_display.setText("🧠 Brain is thinking...")
        QApplication.processEvents()
        
        try:
            # Ask Brain
            response = self.brain.ask(query, mode="balanced")
            
            # Show result
            preview = response[:300].replace('\n', ' ')
            self.result_display.setText(f"✅ Brain: {preview}...")
            
            # Also get plugin suggestions based on response
            context = PluginContext(clipboard_text=query + "\n" + response)
            suggestions = self.plugin_manager.get_suggestions(context)
            
            self.suggestions_list.clear()
            for sug in suggestions[:8]:
                item = QListWidgetItem(f"💡 {sug.title}")
                item.setData(Qt.ItemDataRole.UserRole, sug)
                self.suggestions_list.addItem(item)
            
        except Exception as e:
            self.result_display.setText(f"❌ Error: {str(e)[:100]}")
    
    def execute_suggestion(self, item):
        """Execute a selected suggestion"""
        suggestion = item.data(Qt.ItemDataRole.UserRole)
        self.result_display.setText(f"🚀 Executing: {suggestion.title}\n{suggestion.description}")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_Return and not self.query_input.hasFocus():
            self.process_query()
    
    def show_panel(self):
        """Show panel at cursor position"""
        # Position near top-right (like menu bar dropdown)
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 50
        y = 50
        self.move(x, y)
        self.show()
        self.query_input.setFocus()
        self.auto_detect()  # Immediate detection


class SynthMenuBar(rumps.App):
    """macOS Menu Bar Application"""
    
    def __init__(self):
        super().__init__(
            "Synth",
            icon="🧠",  # Brain emoji as icon
            quit_button=None
        )
        
        # Menu items
        self.menu = [
            rumps.MenuItem("Open Assistant", callback=self.open_panel),
            rumps.separator,
            rumps.MenuItem("Quick Analyze", callback=self.quick_analyze),
            rumps.MenuItem("Screenshot + Analyze", callback=self.screenshot_analyze),
            rumps.separator,
            rumps.MenuItem("Settings", callback=self.show_settings),
            rumps.MenuItem("About", callback=self.show_about),
            rumps.separator,
            rumps.MenuItem("Quit Synth", callback=self.quit_app)
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
            rumps.notification(
                "Synth",
                "Analyzing clipboard...",
                f"{clipboard[:50]}...",
                sound=False
            )
            self.panel.show_panel()
        else:
            rumps.alert("Clipboard is empty", "Copy something first!")
    
    def screenshot_analyze(self, _):
        """Take screenshot and analyze"""
        rumps.notification(
            "Synth",
            "Taking screenshot...",
            "Smile! 📸",
            sound=False
        )
        # TODO: Implement screenshot + OCR
        
    def show_settings(self, _):
        """Show settings"""
        rumps.alert("Settings", "Settings panel coming soon!")
    
    def show_about(self, _):
        """Show about dialog"""
        rumps.alert(
            "Synth - AI Assistant",
            "Your intelligent macOS companion\n\n"
            "Version: 1.0.0\n"
            "Author: Sushant Sharma\n\n"
            "Features:\n"
            "• AI-powered analysis (Ollama)\n"
            "• 8 intelligent plugins\n"
            "• Real-time suggestions\n"
            "• OCR & screenshot analysis"
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
