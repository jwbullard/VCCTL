#!/usr/bin/env python3
"""
Final Icon System Test
Test the complete Carbon icon integration
"""

import sys
import os
sys.path.insert(0, 'src')

def test_final_icon_system():
    """Test the complete icon system integration."""
    try:
        print("🧪 Testing complete Carbon icon system...")
        
        # Test all imports
        from app.utils.icon_utils import create_icon_image, load_carbon_icon, CARBON_ICON_MAPPING
        from app.utils.carbon_icon_manager import CarbonIconManager
        print("✅ All imports successful")
        
        # Test manager
        manager = CarbonIconManager()
        print(f"✅ Carbon manager working: {manager.carbon_icons_dir}")
        
        # Test key icons that should work
        test_icons = [
            'menu',     # Header menu
            'save',     # Export buttons  
            'delete',   # Delete buttons
            'add',      # Add buttons
            'edit',     # Edit buttons
            'search',   # Search functionality
            'close',    # Close buttons
            'settings', # Settings/filter buttons
            'renew',    # Refresh buttons
            'information', # Help/info buttons
        ]
        
        print(f"\n🔍 Testing {len(test_icons)} critical icons:")
        working_icons = 0
        
        for icon_name in test_icons:
            try:
                # Test if icon is mapped
                if icon_name in CARBON_ICON_MAPPING:
                    carbon_name = CARBON_ICON_MAPPING[icon_name] 
                    
                    # Test if we can load it
                    pixbuf = load_carbon_icon(icon_name, 32)
                    if pixbuf:
                        print(f"   ✅ {icon_name} → {carbon_name} ({pixbuf.get_width()}x{pixbuf.get_height()})")
                        working_icons += 1
                    else:
                        print(f"   ❌ {icon_name} → {carbon_name} (failed to load)")
                else:
                    # Try direct loading
                    pixbuf = load_carbon_icon(icon_name, 32)
                    if pixbuf:
                        print(f"   ✅ {icon_name} (direct) ({pixbuf.get_width()}x{pixbuf.get_height()})")
                        working_icons += 1
                    else:
                        print(f"   ❌ {icon_name} (not mapped and failed direct)")
            except Exception as e:
                print(f"   ❌ {icon_name}: error - {e}")
        
        print(f"\n📊 Results: {working_icons}/{len(test_icons)} icons working ({working_icons/len(test_icons)*100:.1f}%)")
        
        # Test create_icon_image function
        try:
            image = create_icon_image("menu", 24)
            print("✅ create_icon_image() working")
        except Exception as e:
            print(f"❌ create_icon_image() failed: {e}")
        
        # Check icon directory structure
        icon_sizes = []
        for size_dir in ['16', '20', '24', '32']:
            size_path = manager.carbon_icons_dir / size_dir
            if size_path.exists():
                icon_count = len(list(size_path.glob("*.svg")))
                icon_sizes.append(f"{size_dir}px({icon_count} icons)")
        
        print(f"📂 Available icon sizes: {', '.join(icon_sizes)}")
        
        if working_icons >= 8:
            print(f"\n🎉 Carbon icon system is working! Most icons should display correctly.")
            print(f"💡 If you still see gray rectangles, there might be size issues or missing specific icons.")
        else:
            print(f"\n⚠️  Icon system has issues - only {working_icons} icons working properly.")
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_icon_system()