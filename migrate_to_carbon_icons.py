#!/usr/bin/env python3
"""
VCCTL Carbon Icon Migration Tool

Analyzes current icon usage and provides automated migration to Carbon Design System icons.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

@dataclass
class IconUsage:
    """Represents an icon usage in the codebase."""
    file_path: str
    line_number: int
    line_content: str
    icon_name: str
    usage_type: str  # 'button_with_icon', 'set_icon_name', 'from_icon_name', etc.
    carbon_suggestion: Optional[str] = None

class VCCTLIconMigrator:
    """Tool for migrating VCCTL icons to Carbon Design System."""
    
    def __init__(self):
        self.src_path = Path("src")
        self.icon_usages = []
        
        # Extended GTK → Carbon mapping (includes the ones from icon_utils.py)
        self.carbon_mappings = {
            # Navigation
            "go-previous": "arrow--left",
            "go-next": "arrow--right", 
            "go-up": "arrow--up",
            "go-down": "arrow--down",
            "go-home": "home",
            "go-first": "skip--back",
            "go-last": "skip--forward",
            
            # File operations
            "document-save": "save",
            "document-open": "folder--open",
            "document-new": "add-alt",
            "document-export": "export",
            "document-print": "printer",
            "document-save-symbolic": "save",
            "document-new-symbolic": "add-alt",
            "document-save-as-symbolic": "export",
            "folder": "folder",
            "folder-open": "folder--open", 
            "folder-new": "folder--add",
            
            # Actions
            "list-add": "add",
            "list-remove": "subtract",
            "list-add-symbolic": "add",
            "list-remove-symbolic": "subtract",
            "edit-delete": "trash-can",
            "edit-copy": "copy",
            "edit-cut": "cut",
            "edit-paste": "paste",
            
            # Media
            "media-playback-start": "play",
            "media-playback-pause": "pause",
            "media-playback-stop": "stop",
            
            # System
            "view-refresh": "refresh",
            "preferences-system": "settings",
            "preferences-desktop": "settings",
            "system-search": "search",
            "search": "search",
            
            # Status and dialogs
            "dialog-information": "information",
            "dialog-warning": "warning",
            "dialog-error": "error",
            "dialog-question": "help",
            
            # Help and info
            "help-contents": "help",
            "help-about": "information",
            "help-browser": "help",
            
            # Tools and utilities
            "accessories-calculator-symbolic": "calculator",
            "utilities-terminal": "terminal",
            
            # Bookmarks
            "bookmark-new": "bookmark--add",
            
            # Menu and UI
            "open-menu-symbolic": "menu",
            "window-close": "close",
            
            # Images and media
            "image-x-generic": "image",
            
            # Special
            "gtk-save": "save",
        }
        
        # Patterns for finding icon usage
        self.patterns = [
            # create_button_with_icon("Label", "icon-name", size)
            (r'create_button_with_icon\(\s*["\']([^"\']*)["\'],\s*["\']([^"\']*)["\'](?:,\s*\d+)?\s*\)', 'button_with_icon'),
            
            # set_icon_name("icon-name")
            (r'\.set_icon_name\(\s*["\']([^"\']*)["\']', 'set_icon_name'),
            
            # new_from_icon_name("icon-name", size)
            (r'\.new_from_icon_name\(\s*["\']([^"\']*)["\']', 'from_icon_name'),
            
            # set_from_icon_name("icon-name", size)
            (r'\.set_from_icon_name\(\s*["\']([^"\']*)["\']', 'set_from_icon_name'),
            
            # Button.new_from_icon_name("icon-name", size)
            (r'Button\.new_from_icon_name\(\s*["\']([^"\']*)["\']', 'button_from_icon_name'),
        ]
    
    def scan_codebase(self) -> List[IconUsage]:
        """Scan the codebase for icon usage."""
        print("🔍 Scanning VCCTL codebase for icon usage...")
        
        python_files = list(self.src_path.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    self._process_line(str(file_path), line_num, line.strip())
                    
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
        
        print(f"📊 Found {len(self.icon_usages)} icon usages across {len(python_files)} files")
        return self.icon_usages
    
    def _process_line(self, file_path: str, line_num: int, line: str):
        """Process a single line for icon patterns."""
        for pattern, usage_type in self.patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                if usage_type == 'button_with_icon':
                    # For create_button_with_icon, the icon is the second capture group
                    label = match.group(1)
                    icon_name = match.group(2)
                else:
                    # For other patterns, icon is the first capture group
                    icon_name = match.group(1)
                
                carbon_suggestion = self.carbon_mappings.get(icon_name)
                
                usage = IconUsage(
                    file_path=file_path,
                    line_number=line_num,
                    line_content=line,
                    icon_name=icon_name,
                    usage_type=usage_type,
                    carbon_suggestion=carbon_suggestion
                )
                self.icon_usages.append(usage)
    
    def analyze_usage(self) -> Dict:
        """Analyze icon usage patterns."""
        analysis = {
            'total_usages': len(self.icon_usages),
            'unique_icons': len(set(usage.icon_name for usage in self.icon_usages)),
            'mappable_icons': len([u for u in self.icon_usages if u.carbon_suggestion]),
            'unmappable_icons': len([u for u in self.icon_usages if not u.carbon_suggestion]),
            'usage_types': {},
            'most_used_icons': {},
            'unmapped_icons': set()
        }
        
        # Count usage types
        for usage in self.icon_usages:
            usage_type = usage.usage_type
            analysis['usage_types'][usage_type] = analysis['usage_types'].get(usage_type, 0) + 1
        
        # Count icon frequency
        for usage in self.icon_usages:
            icon = usage.icon_name
            analysis['most_used_icons'][icon] = analysis['most_used_icons'].get(icon, 0) + 1
            
            if not usage.carbon_suggestion:
                analysis['unmapped_icons'].add(icon)
        
        # Sort by frequency
        analysis['most_used_icons'] = dict(sorted(
            analysis['most_used_icons'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return analysis
    
    def generate_migration_report(self) -> str:
        """Generate a comprehensive migration report."""
        analysis = self.analyze_usage()
        
        report = []
        report.append("=" * 60)
        report.append("VCCTL CARBON ICON MIGRATION ANALYSIS")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY:")
        report.append(f"   Total icon usages: {analysis['total_usages']}")
        report.append(f"   Unique icons: {analysis['unique_icons']}")
        report.append(f"   Can be mapped to Carbon: {analysis['mappable_icons']} ({analysis['mappable_icons']/analysis['total_usages']*100:.1f}%)")
        report.append(f"   Need manual review: {analysis['unmappable_icons']} ({analysis['unmappable_icons']/analysis['total_usages']*100:.1f}%)")
        report.append("")
        
        # Usage types
        report.append("🔧 USAGE TYPES:")
        for usage_type, count in analysis['usage_types'].items():
            report.append(f"   {usage_type}: {count} usages")
        report.append("")
        
        # Most used icons
        report.append("🎯 MOST FREQUENTLY USED ICONS:")
        for icon, count in list(analysis['most_used_icons'].items())[:10]:
            carbon_icon = self.carbon_mappings.get(icon, "❌ No mapping")
            report.append(f"   {icon:<25} ({count:2d} uses) → {carbon_icon}")
        report.append("")
        
        # Unmapped icons that need attention
        if analysis['unmapped_icons']:
            report.append("⚠️  ICONS NEEDING MANUAL MAPPING:")
            for icon in sorted(analysis['unmapped_icons']):
                count = analysis['most_used_icons'][icon]
                report.append(f"   {icon:<25} ({count} uses)")
            report.append("")
        
        # Sample migration examples
        report.append("✨ SAMPLE MIGRATIONS:")
        samples = [u for u in self.icon_usages if u.carbon_suggestion][:5]
        for usage in samples:
            report.append(f"   File: {usage.file_path}")
            report.append(f"   Line {usage.line_number}: {usage.line_content}")
            report.append(f"   Migration: '{usage.icon_name}' → '{usage.carbon_suggestion}'")
            report.append("")
        
        return "\n".join(report)
    
    def suggest_missing_mappings(self) -> Dict[str, str]:
        """Suggest Carbon mappings for unmapped icons."""
        # Add Carbon icon manager to suggest alternatives
        sys.path.insert(0, str(Path("src")))
        
        try:
            from app.utils.carbon_icon_manager import get_carbon_icon_manager
            manager = get_carbon_icon_manager()
            
            suggestions = {}
            unmapped = set(usage.icon_name for usage in self.icon_usages if not usage.carbon_suggestion)
            
            for icon_name in unmapped:
                # Try to find similar Carbon icons
                suggested = manager.suggest_icon_for_action(icon_name)
                if suggested:
                    suggestions[icon_name] = suggested
                else:
                    # Try search for similar names
                    search_results = manager.search_icons(icon_name.replace('-', ' '))
                    if search_results:
                        suggestions[icon_name] = search_results[0]
            
            return suggestions
            
        except Exception as e:
            print(f"⚠️  Could not load Carbon manager for suggestions: {e}")
            return {}
    
    def create_migration_script(self, selected_mappings: Dict[str, str] = None) -> str:
        """Create a migration script to update the files."""
        if selected_mappings is None:
            selected_mappings = self.carbon_mappings
        
        script_lines = []
        script_lines.append("#!/usr/bin/env python3")
        script_lines.append('"""Auto-generated VCCTL Carbon icon migration script"""')
        script_lines.append("")
        script_lines.append("import re")
        script_lines.append("from pathlib import Path")
        script_lines.append("")
        script_lines.append("def migrate_icons():")
        script_lines.append('    """Migrate VCCTL icons to Carbon equivalents."""')
        script_lines.append("")
        
        # Group by file for efficient processing
        files_to_update = {}
        for usage in self.icon_usages:
            if usage.carbon_suggestion and usage.icon_name in selected_mappings:
                if usage.file_path not in files_to_update:
                    files_to_update[usage.file_path] = []
                files_to_update[usage.file_path].append(usage)
        
        for file_path, usages in files_to_update.items():
            script_lines.append(f'    # Update {file_path}')
            script_lines.append(f'    file_path = Path("{file_path}")')
            script_lines.append("    with open(file_path, 'r') as f:")
            script_lines.append("        content = f.read()")
            script_lines.append("")
            
            for usage in usages:
                old_icon = usage.icon_name
                new_icon = selected_mappings[old_icon]
                script_lines.append(f'    # Replace "{old_icon}" with "{new_icon}"')
                script_lines.append(f'    content = content.replace(\'"{old_icon}"\', \'"{new_icon}"\')')
                script_lines.append("")
            
            script_lines.append("    with open(file_path, 'w') as f:")
            script_lines.append("        f.write(content)")
            script_lines.append("")
        
        script_lines.append('    print("✅ Migration completed!")')
        script_lines.append("")
        script_lines.append("if __name__ == '__main__':")
        script_lines.append("    migrate_icons()")
        
        return "\n".join(script_lines)

def main():
    """Main migration analysis function."""
    print("🚀 VCCTL Carbon Icon Migration Tool")
    print("=" * 40)
    
    migrator = VCCTLIconMigrator()
    
    # Scan codebase
    usages = migrator.scan_codebase()
    
    # Generate report
    report = migrator.generate_migration_report()
    print(report)
    
    # Save report to file
    with open("icon_migration_report.txt", "w") as f:
        f.write(report)
    print("📄 Full report saved to: icon_migration_report.txt")
    
    # Get suggestions for unmapped icons
    print("\n🤖 Analyzing unmapped icons for Carbon suggestions...")
    suggestions = migrator.suggest_missing_mappings()
    
    if suggestions:
        print("\n💡 SUGGESTED MAPPINGS FOR REVIEW:")
        for gtk_icon, carbon_icon in suggestions.items():
            print(f"   {gtk_icon:<25} → {carbon_icon}")
        
        # Save suggestions
        with open("suggested_icon_mappings.json", "w") as f:
            json.dump(suggestions, f, indent=2)
        print("💾 Suggestions saved to: suggested_icon_mappings.json")
    
    # Create migration script
    print("\n🔧 Creating migration script...")
    migration_script = migrator.create_migration_script()
    
    with open("apply_carbon_migration.py", "w") as f:
        f.write(migration_script)
    print("📝 Migration script saved to: apply_carbon_migration.py")
    
    print("\n" + "=" * 60)
    print("MIGRATION READY!")
    print("=" * 60)
    print("📋 Next steps:")
    print("   1. Review icon_migration_report.txt")
    print("   2. Check suggested_icon_mappings.json for additional mappings")
    print("   3. Run 'python apply_carbon_migration.py' to apply changes")
    print("   4. Test the application to verify icons display correctly")
    
    return len([u for u in usages if not u.carbon_suggestion])

if __name__ == "__main__":
    unmapped_count = main()
    if unmapped_count > 0:
        print(f"\n⚠️  {unmapped_count} icons still need manual mapping")
    sys.exit(0)