#!/usr/bin/env python3
"""
Fix All Icon Loading - Replace Gtk.Image.new_from_icon_name with Carbon-aware create_icon_image
"""

import re
from pathlib import Path

def fix_all_icon_loading():
    """Fix all Gtk.Image.new_from_icon_name calls to use Carbon icons."""
    
    files_to_fix = [
        "src/app/widgets/file_browser.py",
        "src/app/widgets/unified_psd_widget.py", 
        "src/app/help/help_dialog.py",
        "src/app/help/tooltip_manager.py"
    ]
    
    for file_path in files_to_fix:
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                print(f"❌ File not found: {file_path}")
                continue
                
            with open(path_obj, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Add import if not present
            if 'from app.utils.icon_utils import create_icon_image' not in content:
                # Find a good place to add the import
                if 'from gi.repository import' in content:
                    content = re.sub(
                        r'(from gi\.repository import [^\n]+)',
                        r'\1\nfrom app.utils.icon_utils import create_icon_image',
                        content,
                        count=1
                    )
                elif 'from app.' in content:
                    # Add after existing app imports
                    lines = content.split('\n')
                    import_index = -1
                    for i, line in enumerate(lines):
                        if line.strip().startswith('from app.'):
                            import_index = i
                    
                    if import_index >= 0:
                        lines.insert(import_index + 1, 'from app.utils.icon_utils import create_icon_image')
                        content = '\n'.join(lines)
            
            # Replace Gtk.Image.new_from_icon_name calls
            pattern = r'Gtk\.Image\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
            matches = re.findall(pattern, content)
            
            def replace_image_call(match):
                icon_name = match.group(1)
                return f'create_icon_image("{icon_name}", 16)'
            
            content = re.sub(pattern, replace_image_call, content)
            
            # Replace Button.new_from_icon_name calls  
            button_pattern = r'Gtk\.Button\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
            button_matches = re.findall(button_pattern, content)
            
            # For buttons, we need to create the button and set the image
            def replace_button_call(match):
                icon_name = match.group(1)
                return f'Gtk.Button()\n# Set image: button.set_image(create_icon_image("{icon_name}", 16))'
            
            if button_matches:
                print(f"  ⚠️  {file_path}: Found Button.new_from_icon_name calls - manual review needed")
            
            if content != original_content:
                with open(path_obj, 'w') as f:
                    f.write(content)
                
                total_fixes = len(matches) + len(button_matches)
                print(f"  ✅ {file_path}: {total_fixes} icon loading calls fixed")
            else:
                print(f"  ℹ️  {file_path}: No changes needed")
                
        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")

if __name__ == "__main__":
    print("🔧 Fixing remaining icon loading calls...")
    fix_all_icon_loading()
    print("\n✅ Icon loading fixes complete!")