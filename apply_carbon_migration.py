#!/usr/bin/env python3
"""Auto-generated VCCTL Carbon icon migration script"""

import re
from pathlib import Path

def migrate_icons():
    """Migrate VCCTL icons to Carbon equivalents."""

    # Update src/app/windows/main_window.py
    file_path = Path("src/app/windows/main_window.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "open-menu-symbolic" with "menu"
    content = content.replace('"open-menu-symbolic"', '"menu"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/widgets/material_table.py
    file_path = Path("src/app/widgets/material_table.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "document-save-symbolic" with "save"
    content = content.replace('"document-save-symbolic"', '"save"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/widgets/unified_psd_widget.py
    file_path = Path("src/app/widgets/unified_psd_widget.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "help-about" with "information"
    content = content.replace('"help-about"', '"information"')

    # Replace "help-about" with "information"
    content = content.replace('"help-about"', '"information"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/widgets/file_browser.py
    file_path = Path("src/app/widgets/file_browser.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "go-previous" with "arrow--left"
    content = content.replace('"go-previous"', '"arrow--left"')

    # Replace "go-up" with "arrow--up"
    content = content.replace('"go-up"', '"arrow--up"')

    # Replace "go-home" with "home"
    content = content.replace('"go-home"', '"home"')

    # Replace "view-refresh" with "refresh"
    content = content.replace('"view-refresh"', '"refresh"')

    # Replace "folder-new" with "folder--add"
    content = content.replace('"folder-new"', '"folder--add"')

    # Replace "preferences-desktop" with "settings"
    content = content.replace('"preferences-desktop"', '"settings"')

    # Replace "folder-open" with "folder--open"
    content = content.replace('"folder-open"', '"folder--open"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/help/tooltip_manager.py
    file_path = Path("src/app/help/tooltip_manager.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "help-contents" with "help"
    content = content.replace('"help-contents"', '"help"')

    # Replace "dialog-error" with "error"
    content = content.replace('"dialog-error"', '"error"')

    # Replace "dialog-information" with "information"
    content = content.replace('"dialog-information"', '"information"')

    # Replace "help-contents" with "help"
    content = content.replace('"help-contents"', '"help"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/help/help_dialog.py
    file_path = Path("src/app/help/help_dialog.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "go-previous" with "arrow--left"
    content = content.replace('"go-previous"', '"arrow--left"')

    # Replace "go-next" with "arrow--right"
    content = content.replace('"go-next"', '"arrow--right"')

    # Replace "go-home" with "home"
    content = content.replace('"go-home"', '"home"')

    # Replace "search" with "search"
    content = content.replace('"search"', '"search"')

    # Replace "document-print" with "printer"
    content = content.replace('"document-print"', '"printer"')

    # Replace "bookmark-new" with "bookmark--add"
    content = content.replace('"bookmark-new"', '"bookmark--add"')

    # Replace "list-remove" with "subtract"
    content = content.replace('"list-remove"', '"subtract"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/panels/elastic_moduli_panel.py
    file_path = Path("src/app/windows/panels/elastic_moduli_panel.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "document-save" with "save"
    content = content.replace('"document-save"', '"save"')

    # Replace "media-playback-start" with "play"
    content = content.replace('"media-playback-start"', '"play"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/panels/hydration_panel.py
    file_path = Path("src/app/windows/panels/hydration_panel.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "view-refresh" with "refresh"
    content = content.replace('"view-refresh"', '"refresh"')

    # Replace "document-export" with "export"
    content = content.replace('"document-export"', '"export"')

    # Replace "document-open" with "folder--open"
    content = content.replace('"document-open"', '"folder--open"')

    # Replace "view-refresh" with "refresh"
    content = content.replace('"view-refresh"', '"refresh"')

    # Replace "document-open" with "folder--open"
    content = content.replace('"document-open"', '"folder--open"')

    # Replace "document-save" with "save"
    content = content.replace('"document-save"', '"save"')

    # Replace "media-playback-start" with "play"
    content = content.replace('"media-playback-start"', '"play"')

    # Replace "media-playback-pause" with "pause"
    content = content.replace('"media-playback-pause"', '"pause"')

    # Replace "media-playback-stop" with "stop"
    content = content.replace('"media-playback-stop"', '"stop"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/panels/materials_panel.py
    file_path = Path("src/app/windows/panels/materials_panel.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "list-add-symbolic" with "add"
    content = content.replace('"list-add-symbolic"', '"add"')

    # Replace "document-save-symbolic" with "save"
    content = content.replace('"document-save-symbolic"', '"save"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/panels/aggregate_panel.py
    file_path = Path("src/app/windows/panels/aggregate_panel.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "document-new-symbolic" with "add-alt"
    content = content.replace('"document-new-symbolic"', '"add-alt"')

    # Replace "document-save-symbolic" with "save"
    content = content.replace('"document-save-symbolic"', '"save"')

    # Replace "document-save-as-symbolic" with "export"
    content = content.replace('"document-save-as-symbolic"', '"export"')

    # Replace "list-add-symbolic" with "add"
    content = content.replace('"list-add-symbolic"', '"add"')

    # Replace "accessories-calculator-symbolic" with "calculator"
    content = content.replace('"accessories-calculator-symbolic"', '"calculator"')

    # Replace "list-remove-symbolic" with "subtract"
    content = content.replace('"list-remove-symbolic"', '"subtract"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/panels/mix_design_panel.py
    file_path = Path("src/app/windows/panels/mix_design_panel.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "document-new-symbolic" with "add-alt"
    content = content.replace('"document-new-symbolic"', '"add-alt"')

    # Replace "document-save-symbolic" with "save"
    content = content.replace('"document-save-symbolic"', '"save"')

    # Replace "list-add-symbolic" with "add"
    content = content.replace('"list-add-symbolic"', '"add"')

    # Replace "document-save-as-symbolic" with "export"
    content = content.replace('"document-save-as-symbolic"', '"export"')

    # Replace "list-remove-symbolic" with "subtract"
    content = content.replace('"list-remove-symbolic"', '"subtract"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/panels/microstructure_panel.py
    file_path = Path("src/app/windows/panels/microstructure_panel.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "document-open" with "folder--open"
    content = content.replace('"document-open"', '"folder--open"')

    # Replace "document-export" with "export"
    content = content.replace('"document-export"', '"export"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/panels/operations_monitoring_panel.py
    file_path = Path("src/app/windows/panels/operations_monitoring_panel.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "media-playback-start" with "play"
    content = content.replace('"media-playback-start"', '"play"')

    # Replace "media-playback-stop" with "stop"
    content = content.replace('"media-playback-stop"', '"stop"')

    # Replace "media-playback-pause" with "pause"
    content = content.replace('"media-playback-pause"', '"pause"')

    # Replace "edit-delete" with "trash-can"
    content = content.replace('"edit-delete"', '"trash-can"')

    # Replace "view-refresh" with "refresh"
    content = content.replace('"view-refresh"', '"refresh"')

    # Replace "preferences-system" with "settings"
    content = content.replace('"preferences-system"', '"settings"')

    # Replace "media-playback-pause" with "pause"
    content = content.replace('"media-playback-pause"', '"pause"')

    # Replace "media-playback-stop" with "stop"
    content = content.replace('"media-playback-stop"', '"stop"')

    # Replace "document-export" with "export"
    content = content.replace('"document-export"', '"export"')

    # Replace "view-refresh" with "refresh"
    content = content.replace('"view-refresh"', '"refresh"')

    # Replace "folder-open" with "folder--open"
    content = content.replace('"folder-open"', '"folder--open"')

    # Replace "edit-delete" with "trash-can"
    content = content.replace('"edit-delete"', '"trash-can"')

    # Replace "view-refresh" with "refresh"
    content = content.replace('"view-refresh"', '"refresh"')

    # Replace "document-export" with "export"
    content = content.replace('"document-export"', '"export"')

    # Replace "dialog-information" with "information"
    content = content.replace('"dialog-information"', '"information"')

    with open(file_path, 'w') as f:
        f.write(content)

    # Update src/app/windows/dialogs/material_dialog.py
    file_path = Path("src/app/windows/dialogs/material_dialog.py")
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace "dialog-error" with "error"
    content = content.replace('"dialog-error"', '"error"')

    # Replace "dialog-warning" with "warning"
    content = content.replace('"dialog-warning"', '"warning"')

    # Replace "image-x-generic" with "image"
    content = content.replace('"image-x-generic"', '"image"')

    # Replace "dialog-information" with "information"
    content = content.replace('"dialog-information"', '"information"')

    # Replace "dialog-information" with "information"
    content = content.replace('"dialog-information"', '"information"')

    # Replace "dialog-information" with "information"
    content = content.replace('"dialog-information"', '"information"')

    # Replace "dialog-information" with "information"
    content = content.replace('"dialog-information"', '"information"')

    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Migration completed!")

if __name__ == '__main__':
    migrate_icons()