"""
🎯 SYNTH MENU BAR APP - SIRI STYLE (SIMPLE) 🎯
macOS Menu Bar Application with inline text input

Author: Sushant Sharma
"""

import sys
import rumps
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from brain_client import DeltaBrain
from src.senses.screen_capture import ScreenCapture


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
    print("🚀 Starting Synth Menu Bar App (Simple)...")
    
    # Create and run menu bar app
    app = SynthMenuBar()
    app.run()


if __name__ == "__main__":
    main()
