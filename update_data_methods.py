#!/usr/bin/env python3
"""
Update Data Collection/Loading Methods

This script updates all remaining material dialogs to use the unified PSD widget
for data collection and loading.
"""

import re

def update_data_methods():
    """Update data collection and loading methods for all dialogs."""
    
    dialog_file = "/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/src/app/windows/dialogs/material_dialog.py"
    
    print("🔧 Updating Data Collection/Loading Methods")
    print("=" * 50)
    
    # Read the file
    with open(dialog_file, 'r') as f:
        content = f.read()
    
    print(f"✅ Read material_dialog.py ({len(content.splitlines())} lines)")
    
    # Define the dialogs to update (we already did FlyAsh manually)
    dialogs_to_update = [
        'SlagDialog',
        'LimestoneDialog', 
        'SilicaFumeDialog',
        'InertFillerDialog'
    ]
    
    changes_made = 0
    
    # Common PSD data collection replacement
    psd_collect_patterns = [
        # Pattern 1: Simple median/spread collection
        r'# Add PSD parameters.*?data\[\'psd_spread\'\] = self\.psd_spread_spin\.get_value\(\)',
        # Pattern 2: Custom points collection  
        r'# Include imported PSD data.*?data\[\'psd_custom_points\'\] = json\.dumps\(psd_points\)',
        # Pattern 3: Any PSD-related data collection
        r'# Add PSD.*?data\[\'psd.*?\].*?(?=\n\s{8}[^#\s]|\n\s{4}return|\Z)',
    ]
    
    psd_collect_replacement = '''# Add PSD data from unified widget
        if hasattr(self, 'psd_widget') and self.psd_widget:
            psd_data = self.psd_widget.get_material_data_dict()
            data.update(psd_data)'''
    
    # Common PSD data loading replacement
    psd_load_patterns = [
        # Pattern 1: Simple parameter loading
        r'# Load PSD parameters.*?self\.psd_spread_spin\.set_value\(.*?\)',
        # Pattern 2: Custom data loading with JSON
        r'# Load custom PSD data.*?self\._update_psd_summary_label\(\)',
        # Pattern 3: Any PSD loading block
        r'# Load.*?PSD.*?(?=\n\s{8}# [^P]|\n\s{8}self\._update|\n\s{4}def|\Z)',
    ]
    
    psd_load_replacement = '''# Load PSD data into unified widget
        if hasattr(self, 'psd_widget') and self.psd_widget:
            self.psd_widget.load_from_material_data(self.material_data)'''
    
    for dialog_class in dialogs_to_update:
        print(f"\n🎯 Processing {dialog_class}...")
        
        # Find the class
        class_pattern = rf'class {dialog_class}\(MaterialDialogBase\):'
        class_match = re.search(class_pattern, content)
        
        if not class_match:
            print(f"  ❌ Could not find {dialog_class}")
            continue
        
        class_start = class_match.start()
        
        # Find the next class to establish bounds
        next_class_pattern = r'class \w+Dialog\(MaterialDialogBase\):'
        next_class_matches = list(re.finditer(next_class_pattern, content))
        
        class_end = len(content)
        for match in next_class_matches:
            if match.start() > class_start:
                class_end = match.start()
                break
        
        # Extract class content
        class_content = content[class_start:class_end]
        original_class_content = class_content
        
        # Update _collect_material_specific_data method
        collect_method_pattern = r'def _collect_material_specific_data\(self\) -> Dict\[str, Any\]:(.*?)(?=\n    def [^_]|\nclass |\Z)'
        collect_match = re.search(collect_method_pattern, class_content, re.DOTALL)
        
        if collect_match:
            collect_method_content = collect_match.group(1)
            updated_collect_content = collect_method_content
            
            # Try to replace PSD collection patterns
            for pattern in psd_collect_patterns:
                if re.search(pattern, updated_collect_content, re.DOTALL):
                    updated_collect_content = re.sub(pattern, psd_collect_replacement, updated_collect_content, flags=re.DOTALL)
                    print(f"  ✅ Updated _collect_material_specific_data PSD section")
                    break
            
            # Replace in class content
            class_content = class_content.replace(collect_method_content, updated_collect_content)
        
        # Update _load_material_specific_data method
        load_method_pattern = r'def _load_material_specific_data\(self\) -> None:(.*?)(?=\n    def [^_]|\nclass |\Z)'
        load_match = re.search(load_method_pattern, class_content, re.DOTALL)
        
        if load_match:
            load_method_content = load_match.group(1)
            updated_load_content = load_method_content
            
            # Try to replace PSD loading patterns
            for pattern in psd_load_patterns:
                if re.search(pattern, updated_load_content, re.DOTALL):
                    updated_load_content = re.sub(pattern, psd_load_replacement, updated_load_content, flags=re.DOTALL)
                    print(f"  ✅ Updated _load_material_specific_data PSD section")
                    break
            
            # Replace in class content
            class_content = class_content.replace(load_method_content, updated_load_content)
        
        # If we made changes to this class, update the main content
        if class_content != original_class_content:
            content = content[:class_start] + class_content + content[class_end:]
            changes_made += 1
            print(f"  ✅ Updated {dialog_class} data methods")
        else:
            print(f"  ⚠️  No PSD data methods found in {dialog_class}")
    
    if changes_made > 0:
        # Write back to file
        with open(dialog_file, 'w') as f:
            f.write(content)
        
        print(f"\n🎉 SUCCESS: Updated data methods for {changes_made} dialogs!")
        print("✅ All dialogs now use unified PSD widget for data operations")
    else:
        print(f"\n❌ No changes made")

if __name__ == "__main__":
    update_data_methods()