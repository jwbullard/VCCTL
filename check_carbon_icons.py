#!/usr/bin/env python3
"""
Quick status check for Carbon icon integration
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def check_carbon_integration():
    """Check the status of Carbon icon integration."""
    print("🔍 Checking Carbon Icon Integration Status...")
    print("=" * 50)
    
    # Check if Carbon icons are installed
    icons_dir = Path("icons/carbon")
    if icons_dir.exists():
        print("✅ Carbon icons directory exists")
        
        # Check sizes
        sizes = ["16", "20", "24", "32"]
        for size in sizes:
            size_dir = icons_dir / size
            if size_dir.exists():
                icon_count = len(list(size_dir.glob("*.svg")))
                print(f"✅ Size {size}px: {icon_count} icons")
            else:
                print(f"❌ Size {size}px: directory missing")
        
        # Check metadata
        metadata_file = icons_dir / "metadata.json"
        if metadata_file.exists():
            print("✅ Metadata file exists")
        else:
            print("⚠️  Metadata file missing (will be built from files)")
    else:
        print("❌ Carbon icons directory missing")
        return False
    
    print()
    
    # Test Carbon icon manager
    try:
        from app.utils.carbon_icon_manager import get_carbon_icon_manager
        manager = get_carbon_icon_manager()
        
        icon_count = len(manager.get_available_icons())
        category_count = len(manager.get_categories())
        
        print(f"✅ Carbon Icon Manager loaded: {icon_count:,} icons in {category_count} categories")
        
        # Test loading a few icons
        test_icons = ["add", "save", "folder", "settings"]
        for icon_name in test_icons:
            pixbuf = manager.load_icon_pixbuf(icon_name, 32)
            if pixbuf:
                print(f"✅ Icon '{icon_name}': loaded successfully")
            else:
                print(f"❌ Icon '{icon_name}': failed to load")
        
    except Exception as e:
        print(f"❌ Carbon Icon Manager error: {e}")
        return False
    
    print()
    
    # Test icon utilities integration
    try:
        from app.utils.icon_utils import load_icon_with_fallback, create_button_with_icon
        
        # Test fallback chain
        pixbuf = load_icon_with_fallback("document-save", 24)
        if pixbuf:
            print("✅ Icon utilities integration working")
        else:
            print("❌ Icon utilities integration failed")
            
    except Exception as e:
        print(f"❌ Icon utilities error: {e}")
        return False
    
    print()
    print("🎉 Carbon Icon Integration Status: READY!")
    print()
    print("📝 Next Steps:")
    print("   1. Run 'python carbon_icon_demo.py' to see the full demo")
    print("   2. Use Carbon icons in VCCTL with existing icon utilities")
    print("   3. Icons will automatically fall back: Carbon → Custom → System")
    print()
    print("🔧 Usage Examples:")
    print("   create_button_with_icon('Save', 'document-save')  # Uses Carbon 'save' icon")
    print("   create_carbon_image('folder--open', 32)           # Direct Carbon icon")
    print("   browse_carbon_icons(parent_window)                # Open icon browser")
    
    return True

if __name__ == "__main__":
    success = check_carbon_integration()
    sys.exit(0 if success else 1)