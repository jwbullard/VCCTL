#!/usr/bin/env python3
"""
Visual test for enhanced AggregateDialog with fixes applied.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from app.services.service_container import ServiceContainer
from app.windows.dialogs.material_dialog import AggregateDialog

class MockMainWindow(Gtk.Window):
    """Mock main window for testing dialog."""
    def __init__(self):
        super().__init__()
        self.service_container = ServiceContainer()
        self.set_title("Mock Main Window")
        self.set_default_size(400, 300)
    
    def update_status(self, message, type, duration):
        print(f"Status: {message} ({type})")

def test_aggregate_dialog():
    """Test the enhanced AggregateDialog with actual aggregate data."""
    print("Testing Enhanced AggregateDialog with fixes...")
    
    # Get aggregate service
    service_container = ServiceContainer()
    aggregate_service = service_container.aggregate_service
    
    # Get first aggregate
    aggregates = aggregate_service.get_all()
    if not aggregates:
        print("❌ No aggregates found in database")
        return
    
    test_aggregate = aggregates[0]
    print(f"Testing with aggregate: {test_aggregate.display_name}")
    
    # Create mock main window
    mock_window = MockMainWindow()
    
    # Create dialog with aggregate data
    material_data = {
        'id': test_aggregate.id,
        'display_name': test_aggregate.display_name,
        'name': test_aggregate.name,
        'specific_gravity': test_aggregate.specific_gravity,
        'bulk_modulus': test_aggregate.bulk_modulus,
        'shear_modulus': test_aggregate.shear_modulus,
        'conductivity': test_aggregate.conductivity,
        'txt': test_aggregate.txt,
        'notes': test_aggregate.notes,
        'source': test_aggregate.source
    }
    
    dialog = AggregateDialog(mock_window, material_data)
    
    def on_dialog_response(dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            print("✅ Dialog completed successfully")
        else:
            print("Dialog cancelled or closed")
        Gtk.main_quit()
    
    dialog.connect('response', on_dialog_response)
    dialog.show_all()
    
    print("🎉 Enhanced AggregateDialog opened!")
    print("Expected fixes:")
    print("  1. ✅ Properties tab layout should be clean (no corruption)")
    print("  2. ✅ PNG image should appear for", test_aggregate.display_name)
    print("  3. ✅ Description should show source, notes, and properties")
    print("  4. ✅ Shape statistics should display in left panel")
    print("\nClose dialog to exit test...")
    
    Gtk.main()

if __name__ == '__main__':
    test_aggregate_dialog()