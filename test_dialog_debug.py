#!/usr/bin/env python3
"""
Debug script for GradingManagementDialog blank content issue
"""
import sys
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_dialog_creation():
    """Test dialog creation step by step"""
    try:
        print("1. Importing dependencies...")
        from app.database.service import DatabaseService
        from app.windows.dialogs.grading_management_dialog import GradingManagementDialog
        print("✓ Imports successful")
        
        print("2. Creating database service...")
        db_service = DatabaseService()
        print("✓ Database service created")
        
        print("3. Creating dialog...")
        dialog = GradingManagementDialog(None, db_service)
        print("✓ Dialog created")
        
        print("4. Showing dialog...")
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        print("✓ Dialog completed")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dialog_creation()