#!/usr/bin/env python3
"""
Fix Icon Loading System
Replaces direct Gtk.Image.new_from_icon_name() calls with Carbon-aware icon utilities
"""

import re
from pathlib import Path

def fix_icon_loading():
    """Replace direct GTK icon loading with Carbon-aware utilities."""
    
    replacements_made = 0
    files_modified = 0
    
    # Find all Python files in src directory
    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src directory not found!")
        return
    
    print("🔧 Fixing icon loading to use Carbon icons...")
    
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Check if file already imports icon_utils
            has_icon_utils_import = 'from app.utils.icon_utils import' in content or 'import app.utils.icon_utils' in content
            
            # Pattern 1: Gtk.Image.new_from_icon_name("icon-name", Gtk.IconSize.BUTTON)
            pattern1 = r'Gtk\.Image\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
            matches1 = re.findall(pattern1, content)
            
            # Pattern 2: Gtk.Button.new_from_icon_name("icon-name", Gtk.IconSize.BUTTON)
            pattern2 = r'Gtk\.Button\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
            matches2 = re.findall(pattern2, content)
            
            if matches1 or matches2:
                # Add import if needed
                if not has_icon_utils_import:
                    # Find the best place to add import (after other app imports)
                    if 'from app.' in content:
                        # Add after last app import
                        lines = content.split('\n')
                        import_index = -1
                        for i, line in enumerate(lines):
                            if line.strip().startswith('from app.'):
                                import_index = i
                        
                        if import_index >= 0:
                            lines.insert(import_index + 1, 'from app.utils.icon_utils import create_icon_image')
                            content = '\n'.join(lines)
                    else:
                        # Add after gi imports
                        if 'from gi.repository import' in content:
                            content = re.sub(
                                r'(from gi\.repository import [^\n]+)',
                                r'\1\nfrom app.utils.icon_utils import create_icon_image',
                                content,
                                count=1
                            )
                
                # Replace Pattern 1: Gtk.Image.new_from_icon_name
                def replace_image_creation(match):
                    icon_name = match.group(1)
                    return f'create_icon_image("{icon_name}", 24)'
                
                content = re.sub(pattern1, replace_image_creation, content)
                
                # Replace Pattern 2: Gtk.Button.new_from_icon_name  
                def replace_button_creation(match):
                    icon_name = match.group(1)
                    return f'Gtk.Button()\n# TODO: Set button icon with create_icon_image("{icon_name}", 16)'
                
                # For buttons, we need a more complex replacement
                button_pattern = r'(\w+)\s*=\s*Gtk\.Button\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
                def replace_button_with_icon(match):
                    var_name = match.group(1)
                    icon_name = match.group(2)
                    return f'''{var_name} = Gtk.Button()
        {var_name}.set_image(create_icon_image("{icon_name}", 16))'''
                
                content = re.sub(button_pattern, replace_button_with_icon, content)
                
                if content != original_content:
                    # Write the file back
                    with open(py_file, 'w') as f:
                        f.write(content)
                    
                    file_changes = len(matches1) + len(matches2)
                    replacements_made += file_changes
                    files_modified += 1
                    print(f"  ✅ {py_file}: {file_changes} icon loading calls fixed")
                    
        except Exception as e:
            print(f"  ❌ Error processing {py_file}: {e}")
    
    print(f"\n🎉 Icon loading fixes completed!")
    print(f"  📁 Files modified: {files_modified}")  
    print(f"  🔄 Icon loading calls fixed: {replacements_made}")

if __name__ == "__main__":
    fix_icon_loading()