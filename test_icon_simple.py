#!/usr/bin/env python3
"""
Simple Icon Test - Test specific icon loading
"""

import sys
import os
sys.path.insert(0, 'src')

def test_icon_loading():
    """Test basic icon loading functionality."""
    try:
        print("🧪 Testing icon loading...")
        
        # Test icon utilities import
        from app.utils.icon_utils import create_icon_image, load_carbon_icon
        print("✅ Icon utilities imported")
        
        # Test Carbon icon manager import
        from app.utils.carbon_icon_manager import CarbonIconManager
        print("✅ Carbon icon manager imported")
        
        # Create manager instance
        manager = CarbonIconManager()
        print(f"✅ Manager created, icons dir: {manager.carbon_icons_dir}")
        
        # Test simple icon loading  
        icons_to_test = ['menu', 'information', 'save', 'renew', 'delete']
        
        for icon_name in icons_to_test:
            try:
                pixbuf = load_carbon_icon(icon_name, 24)
                if pixbuf:
                    print(f"✅ {icon_name}: loaded ({pixbuf.get_width()}x{pixbuf.get_height()})")
                else:
                    print(f"❌ {icon_name}: failed to load")
            except Exception as e:
                print(f"❌ {icon_name}: error - {e}")
        
        # Test icon image creation
        try:
            image = create_icon_image("menu", 24)  
            print("✅ Icon image creation working")
        except Exception as e:
            print(f"❌ Icon image creation failed: {e}")
        
        # Check available icons in directory
        icons_dir = manager.carbon_icons_dir / "32"
        if icons_dir.exists():
            icon_files = list(icons_dir.glob("*.svg"))
            print(f"📊 Found {len(icon_files)} SVG icons in {icons_dir}")
            
            # List a few examples
            for icon_file in sorted(icon_files)[:5]:
                print(f"   • {icon_file.stem}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_icon_loading()