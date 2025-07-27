#!/usr/bin/env python3
"""
Integration Script for Unified PSD Widget

This script integrates the unified PSD widget into all material dialogs,
replacing the old complex PSD implementations.
"""

import re
import sys
import os

def integrate_unified_psd():
    """Integrate unified PSD widget into all material dialogs."""
    
    dialog_file = "/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/src/app/windows/dialogs/material_dialog.py"
    
    print("🔧 Integrating Unified PSD Widget into Material Dialogs")
    print("=" * 60)
    
    # Read the current file
    with open(dialog_file, 'r') as f:
        content = f.read()
    
    print(f"✅ Read material_dialog.py ({len(content.splitlines())} lines)")
    
    # Material types and their corresponding PSD integration
    materials = [
        ('fly_ash', 'FlyAshDialog'),
        ('slag', 'SlagDialog'), 
        ('limestone', 'LimestoneDialog'),
        ('silica_fume', 'SilicaFumeDialog'),
        ('inert_filler', 'InertFillerDialog')
    ]
    
    # Track changes
    changes_made = 0
    
    for material_type, dialog_class in materials:
        print(f"\n🎯 Processing {dialog_class} ({material_type})...")
        
        # Find the dialog class
        class_pattern = rf'class {dialog_class}\(MaterialDialogBase\):'
        class_match = re.search(class_pattern, content)
        
        if not class_match:
            print(f"  ❌ Could not find {dialog_class}")
            continue
        
        class_start = class_match.start()
        print(f"  ✅ Found {dialog_class} at position {class_start}")
        
        # Find the _add_psd_section method within this class
        # Look for the method after the class definition but before the next class
        next_class_pattern = r'class \w+Dialog\(MaterialDialogBase\):'
        next_class_matches = list(re.finditer(next_class_pattern, content))
        
        # Find the next class after the current one
        class_end = len(content)
        for match in next_class_matches:
            if match.start() > class_start:
                class_end = match.start()
                break
        
        # Extract the class content
        class_content = content[class_start:class_end]
        
        # Find _add_psd_section method within this class
        psd_method_pattern = r'def _add_psd_section\(self, container: Gtk\.Box\) -> None:(.*?)(?=\n    def |\n\nclass |\Z)'
        psd_match = re.search(psd_method_pattern, class_content, re.DOTALL)
        
        if not psd_match:
            print(f"  ❌ Could not find _add_psd_section method in {dialog_class}")
            continue
        
        print(f"  ✅ Found _add_psd_section method")
        
        # Create the replacement unified PSD method
        unified_psd_method = f'''def _add_psd_section(self, container: Gtk.Box) -> None:
        """Add unified particle size distribution section."""
        from app.widgets.unified_psd_widget import UnifiedPSDWidget
        
        # Create unified PSD widget for {material_type}
        self.psd_widget = UnifiedPSDWidget('{material_type}')
        self.psd_widget.set_change_callback(self._on_psd_changed)
        
        # Add to container
        container.pack_start(self.psd_widget, True, True, 0)
    
    def _on_psd_changed(self):
        """Handle PSD data changes from unified widget."""
        # Optional: validation or other updates
        pass'''
        
        # Find the position in the original content
        method_start_in_file = class_start + psd_match.start()
        method_end_in_file = class_start + psd_match.end()
        
        # Replace the method in the original content
        content = content[:method_start_in_file] + unified_psd_method + content[method_end_in_file:]
        
        print(f"  ✅ Replaced _add_psd_section method with unified widget")
        changes_made += 1
    
    if changes_made > 0:
        # Write the updated content back to the file
        with open(dialog_file, 'w') as f:
            f.write(content)
        
        print(f"\n🎉 SUCCESS: Integrated unified PSD widget into {changes_made} material dialogs!")
        print("✅ Updated material_dialog.py")
        
        # Display summary
        print(f"\n📊 INTEGRATION SUMMARY:")
        print(f"  • Cement Dialog: ✅ (already completed)")
        for material_type, dialog_class in materials:
            status = "✅" if changes_made > 0 else "❌"
            print(f"  • {dialog_class}: {status}")
        
        print(f"\n🚀 Next Steps:")
        print(f"  1. Update data collection/loading methods for each dialog")
        print(f"  2. Test the integrated widgets")
        print(f"  3. Remove old PSD implementation code")
    else:
        print(f"\n❌ No changes made - could not find target methods")

if __name__ == "__main__":
    integrate_unified_psd()