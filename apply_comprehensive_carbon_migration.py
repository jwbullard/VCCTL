#!/usr/bin/env python3
"""
Comprehensive VCCTL Carbon Icon Migration
Applies all recommended Carbon icon mappings
"""

import re
from pathlib import Path

def migrate_icons():
    """Apply comprehensive Carbon icon mappings."""
    
    # Complete icon mappings based on analysis and recommendations
    mappings = {
        # Most frequently used (high priority)
        "view-refresh": "refresh",
        "dialog-information": "information", 
        "edit-clear": "erase",
        "document-save-symbolic": "save",
        "document-export": "export",
        "media-playback-start": "play",
        "document-open": "folder--open",
        "media-playback-pause": "pause", 
        "media-playback-stop": "stop",
        "list-add-symbolic": "add",
        
        # Navigation icons
        "go-previous": "arrow--left",
        "go-next": "arrow--right", 
        "go-up": "arrow--up",
        "go-first-symbolic": "skip--back",
        "go-last-symbolic": "skip--forward",
        
        # File operations
        "document-open-symbolic": "folder--open",
        "document-edit-symbolic": "edit",
        "folder-new": "folder--add",
        "edit-copy-symbolic": "copy",
        "edit-delete-symbolic": "trash-can",
        "edit-find-symbolic": "search",
        
        # System/settings
        "preferences-system-symbolic": "settings",
        "system-run-symbolic": "play",
        "window-close-symbolic": "close",
        
        # View/interface
        "view-list-symbolic": "list",
        "view-refresh-symbolic": "refresh",
        "open-menu-symbolic": "menu",
        
        # Custom/special
        "48-cube": "cube",
        "help-about": "information",
        
        # Additional common icons
        "dialog-information-symbolic": "information",
        "list-remove-symbolic": "subtract",
        "edit-undo": "undo",
        "edit-redo": "redo",
        "zoom-in": "zoom-in",
        "zoom-out": "zoom-out",
        "view-fullscreen": "fit-to-screen",
        "process-stop": "stop",
        "dialog-warning": "warning",
        "dialog-error": "error",
        "application-exit": "logout",
        "folder-open": "folder--open",
        "text-x-generic": "document",
        "image-x-generic": "image",
        "media-seek-forward": "skip--forward",
        "media-seek-backward": "skip--back",
    }
    
    print(f"🚀 Applying {len(mappings)} Carbon icon mappings...")
    
    # Find all Python files in src directory
    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src directory not found!")
        return
    
    files_modified = 0
    total_replacements = 0
    
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # Apply each mapping
            for old_icon, new_icon in mappings.items():
                # Replace in various icon usage patterns
                patterns = [
                    rf'(new_from_icon_name\(\s*["\']){re.escape(old_icon)}(["\'])',
                    rf'(set_icon_name\(\s*["\']){re.escape(old_icon)}(["\'])',
                    rf'(from_icon_name\(\s*["\']){re.escape(old_icon)}(["\'])',
                    rf'(button_with_icon\([^,]+,\s*["\']){re.escape(old_icon)}(["\'])',
                    rf'(set_from_icon_name\(\s*["\']){re.escape(old_icon)}(["\'])',
                    rf'(button_from_icon_name\(\s*["\']){re.escape(old_icon)}(["\'])',
                ]
                
                for pattern in patterns:
                    matches_before = len(re.findall(pattern, content))
                    content = re.sub(pattern, rf'\1{new_icon}\2', content)
                    matches_after = len(re.findall(pattern, content))
                    
                    if matches_before > matches_after:
                        replacements_made = matches_before - matches_after
                        file_replacements += replacements_made
                        print(f"    {old_icon} → {new_icon} ({replacements_made}x) in {py_file.name}")
            
            # Write back if changed
            if content != original_content:
                with open(py_file, 'w') as f:
                    f.write(content)
                files_modified += 1
                total_replacements += file_replacements
                print(f"  ✅ Modified: {py_file} ({file_replacements} replacements)")
                
        except Exception as e:
            print(f"  ❌ Error processing {py_file}: {e}")
    
    print(f"\n🎉 Migration completed!")
    print(f"  📁 Files modified: {files_modified}")
    print(f"  🔄 Total icon replacements: {total_replacements}")
    print(f"\n💡 Next steps:")
    print(f"  1. Test your VCCTL application")
    print(f"  2. Check that all icons display correctly") 
    print(f"  3. Let Claude know about any icons you want to change")

if __name__ == "__main__":
    migrate_icons()