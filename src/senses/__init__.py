"""
Project Synth - Phase 1: Senses Module

This module handles clipboard and screen monitoring for proactive detection.

Author: Sushant Sharma
Phase: 1 - Detection System
Status: In Development
"""

from .clipboard_monitor import ClipboardMonitor
from .screen_capture import ScreenCapture
from .trigger_system import TriggerSystem

__all__ = ['ClipboardMonitor', 'ScreenCapture', 'TriggerSystem']
