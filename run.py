#!/usr/bin/env python3
"""
Telegram PDF Bot
Main entry point for the application

Author: Your Name
Version: 1.0.0
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run main function
from bot.main import main

if __name__ == '__main__':
    try:
        print("╔════════════════════════════════════════╗")
        print("║   Telegram PDF Bot - Starting...      ║")
        print("╚════════════════════════════════════════╝")
        main()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}\n")
        sys.exit(1)
