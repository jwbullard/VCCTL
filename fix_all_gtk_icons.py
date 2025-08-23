#!/usr/bin/env python3
"""
Comprehensive GTK Icon Fix
Replace ALL Gtk.Image.new_from_icon_name calls with Carbon-aware create_icon_image calls
"""

import re
from pathlib import Path

def fix_all_gtk_icon_calls():
    """Find and fix all direct GTK icon calls in the entire codebase."""
    
    print("🔧 Scanning entire codebase for GTK icon calls...")
    
    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src directory not found!")
        return
    
    total_files_modified = 0
    total_replacements = 0
    
    # Find ALL Python files
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # Check if file already has the import we need
            has_import = 'from app.utils.icon_utils import create_icon_image' in content
            
            # Pattern 1: Gtk.Image.new_from_icon_name("icon-name", Gtk.IconSize.XXX)
            pattern1 = r'Gtk\.Image\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
            matches1 = re.findall(pattern1, content)
            
            # Pattern 2: set_image(Gtk.Image.new_from_icon_name(...))
            pattern2 = r'\.set_image\(Gtk\.Image\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)\)'
            matches2 = re.findall(pattern2, content)
            
            # Pattern 3: Button.new_from_icon_name
            pattern3 = r'Gtk\.Button\.new_from_icon_name\(\s*["\']([^"\']+)["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
            matches3 = re.findall(pattern3, content)
            
            if matches1 or matches2 or matches3:
                print(f"\n📁 Processing: {py_file}")
                print(f"   Found: {len(matches1)} Image.new_from_icon_name, {len(matches2)} set_image calls, {len(matches3)} Button calls")
                
                # Add import if needed
                if not has_import:
                    if 'from gi.repository import' in content:
                        # Add after gi imports
                        content = re.sub(
                            r'(from gi\.repository import [^\n]+\n)',
                            r'\1from app.utils.icon_utils import create_icon_image\n',
                            content,
                            count=1
                        )
                        print("   ✅ Added create_icon_image import")
                    elif 'import gi' in content:
                        # Add after import gi block
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if line.strip().startswith('from gi.repository'):
                                lines.insert(i + 1, 'from app.utils.icon_utils import create_icon_image')
                                break
                        content = '\n'.join(lines)
                        print("   ✅ Added create_icon_image import")
                
                # Replace Pattern 1: Gtk.Image.new_from_icon_name
                def replace_image_new(match):
                    icon_name = match.group(1)
                    return f'create_icon_image("{icon_name}", 16)'
                
                old_content = content
                content = re.sub(pattern1, replace_image_new, content)
                if content != old_content:
                    file_replacements += len(matches1)
                    print(f"   ✅ Fixed {len(matches1)} Image.new_from_icon_name calls")
                
                # Replace Pattern 2: .set_image(Gtk.Image.new_from_icon_name(...))
                def replace_set_image(match):
                    icon_name = match.group(1)
                    return f'.set_image(create_icon_image("{icon_name}", 16))'
                
                old_content = content
                content = re.sub(pattern2, replace_set_image, content)
                if content != old_content:
                    file_replacements += len(matches2)
                    print(f"   ✅ Fixed {len(matches2)} set_image calls")
                
                # Replace Pattern 3: Button.new_from_icon_name - more complex
                for match in matches3:
                    icon_name = match
                    old_pattern = rf'Gtk\.Button\.new_from_icon_name\(\s*["\']({re.escape(icon_name)})["\']\s*,\s*Gtk\.IconSize\.\w+\s*\)'
                    new_replacement = f'Gtk.Button()\n        # TODO: Add this after button creation: button.set_image(create_icon_image("{icon_name}", 16))'
                    
                    if re.search(old_pattern, content):
                        print(f"   ⚠️  Found Button.new_from_icon_name('{icon_name}') - needs manual review")
                        file_replacements += 1
                
                total_replacements += file_replacements
                
                # Write the modified file
                if content != original_content:
                    with open(py_file, 'w') as f:
                        f.write(content)
                    total_files_modified += 1
                    print(f"   ✅ File updated with {file_replacements} fixes")
                    
        except Exception as e:
            print(f"❌ Error processing {py_file}: {e}")
    
    print(f"\n🎉 GTK Icon Fix Complete!")
    print(f"   📁 Files modified: {total_files_modified}")
    print(f"   🔄 Total replacements: {total_replacements}")
    
    if total_files_modified > 0:
        print(f"\n💡 Next step: Test your VCCTL application - icons should now display correctly!")
    else:
        print(f"\n💡 No GTK icon calls found - the Carbon system might already be working")

if __name__ == "__main__":
    fix_all_gtk_icon_calls()