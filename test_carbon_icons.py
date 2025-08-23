#!/usr/bin/env python3
"""
Test Carbon Icon Loading
Verify that Carbon icons are loading correctly
"""

import sys
import os
sys.path.insert(0, 'src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def test_carbon_icons():
    """Test if Carbon icons are loading."""
    print("🧪 Testing Carbon icon system...")
    
    try:
        # Test icon utility import
        from app.utils.icon_utils import create_icon_image, load_carbon_icon, CARBON_ICON_MAPPING
        print("✅ Icon utilities imported successfully")
        
        # Test Carbon icon manager
        from app.utils.carbon_icon_manager import get_carbon_icon_manager
        manager = get_carbon_icon_manager()
        print(f"✅ Carbon icon manager loaded: {len(manager.available_icons)} icons available")
        
        # Test some key icon mappings
        test_icons = ['menu', 'trash-can', 'refresh', 'save', 'information', 'play', 'stop', 'pause']
        
        for icon_name in test_icons:
            if icon_name in CARBON_ICON_MAPPING:
                carbon_name = CARBON_ICON_MAPPING[icon_name]
                print(f"✅ {icon_name} → {carbon_name}")
                
                # Try to load the icon
                pixbuf = load_carbon_icon(icon_name, 24)
                if pixbuf:
                    print(f"  ✅ Icon loaded successfully ({pixbuf.get_width()}x{pixbuf.get_height()})")
                else:
                    print(f"  ❌ Failed to load icon")
            else:
                print(f"❌ {icon_name} not in mapping")
        
        # Test icon creation
        try:
            image = create_icon_image("refresh", 24)
            print("✅ Icon image creation successful")
        except Exception as e:
            print(f"❌ Icon image creation failed: {e}")
        
        print(f"\n📊 Carbon Icon System Status:")
        print(f"   • Icon mappings: {len(CARBON_ICON_MAPPING)}")
        print(f"   • Available Carbon icons: {len(manager.available_icons)}")
        print(f"   • Icon directory: {manager.icons_dir}")
        
    except Exception as e:
        print(f"❌ Error testing icons: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_carbon_icons()