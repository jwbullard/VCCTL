#!/usr/bin/env python3
"""
Helper methods for Mix Design Management functionality.

These methods are separated out to keep the main mix_design_panel.py file manageable.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from gi.repository import Gtk
from app.services.mix_design_service import MixDesignService


def populate_management_mix_design_list(service_container, list_store: Gtk.ListStore) -> None:
    """Populate the management list store with all mix designs."""
    try:
        # Get mix design service
        mix_design_service = MixDesignService(service_container.database_service)
        mix_designs = mix_design_service.get_all()
        
        # Populate list store
        for mix_design in mix_designs:
            # Format created date
            created_date = mix_design.created_at.strftime("%Y-%m-%d %H:%M") if mix_design.created_at else "Unknown"
            
            # Format W/B ratio
            wb_ratio = f"{mix_design.water_binder_ratio:.3f}"
            
            # Check if microstructure exists
            has_microstructure = "Yes" if mix_design.has_generated_microstructure else "No"
            
            # Format description (or use default)
            description = mix_design.description or "No description"
            if len(description) > 50:
                description = description[:47] + "..."
            
            # Add to list store: selected, name, description, created_date, w/b_ratio, has_microstructure, mix_id
            list_store.append([
                False,  # selected
                mix_design.name,
                description,
                created_date,
                wb_ratio,
                has_microstructure,
                mix_design.id
            ])
    
    except Exception as e:
        print(f"Error populating management list: {e}")


def update_management_button_sensitivity(list_store: Gtk.ListStore, bulk_delete_button, duplicate_button, export_button) -> None:
    """Update button sensitivity based on selections."""
    selected_count = sum(1 for row in list_store if row[0])  # Count selected items
    
    # Enable bulk delete if any items selected
    bulk_delete_button.set_sensitive(selected_count > 0)
    
    # Enable duplicate and export only if exactly one item selected
    duplicate_button.set_sensitive(selected_count == 1)
    export_button.set_sensitive(selected_count == 1)


def bulk_delete_mix_designs(service_container, list_store: Gtk.ListStore, status_bar, context_id, main_window) -> None:
    """Delete all selected mix designs after confirmation."""
    try:
        # Get selected items
        selected_items = []
        for row in list_store:
            if row[0]:  # If selected
                selected_items.append({
                    'name': row[1],
                    'id': row[6]
                })
        
        if not selected_items:
            status_bar.push(context_id, "No items selected")
            return
        
        # Confirmation dialog
        confirm_dialog = Gtk.MessageDialog(
            transient_for=main_window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete {len(selected_items)} Mix Designs?"
        )
        confirm_dialog.format_secondary_text(
            f"This will permanently delete:\n" + 
            "\n".join([f"• {item['name']}" for item in selected_items[:10]]) +
            (f"\n... and {len(selected_items) - 10} more" if len(selected_items) > 10 else "") +
            "\n\nThis action cannot be undone."
        )
        
        response = confirm_dialog.run()
        confirm_dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Delete items
            mix_design_service = MixDesignService(service_container.database_service)
            deleted_count = 0
            
            for item in selected_items:
                try:
                    mix_design_service.delete_by_id(item['id'])
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {item['name']}: {e}")
            
            # Refresh list store
            list_store.clear()
            populate_management_mix_design_list(service_container, list_store)
            
            status_bar.push(context_id, f"Deleted {deleted_count} mix designs")
        
    except Exception as e:
        status_bar.push(context_id, f"Error during bulk delete: {e}")


def duplicate_selected_mix_design(service_container, list_store: Gtk.ListStore, status_bar, context_id, main_window) -> None:
    """Duplicate the selected mix design."""
    try:
        # Find selected item
        selected_id = None
        selected_name = None
        for row in list_store:
            if row[0]:  # If selected
                selected_id = row[6]
                selected_name = row[1]
                break
        
        if not selected_id:
            status_bar.push(context_id, "No item selected")
            return
        
        # Get new name from user
        dialog = Gtk.Dialog(
            title="Duplicate Mix Design",
            transient_for=main_window,
            flags=0
        )
        dialog.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Duplicate", Gtk.ResponseType.OK
        )
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        label = Gtk.Label(f"Enter name for duplicate of '{selected_name}':")
        entry = Gtk.Entry()
        entry.set_text(f"{selected_name}_copy")
        entry.select_region(0, -1)  # Select all text
        
        content_area.pack_start(label, False, False, 0)
        content_area.pack_start(entry, False, False, 0)
        
        dialog.show_all()
        response = dialog.run()
        new_name = entry.get_text().strip()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and new_name:
            # Duplicate the mix design
            mix_design_service = MixDesignService(service_container.database_service)
            try:
                duplicated = mix_design_service.duplicate(selected_id, new_name)
                
                # Refresh list store
                list_store.clear()
                populate_management_mix_design_list(service_container, list_store)
                
                status_bar.push(context_id, f"Created duplicate: {duplicated.name}")
                
            except Exception as e:
                status_bar.push(context_id, f"Error duplicating mix design: {e}")
    
    except Exception as e:
        status_bar.push(context_id, f"Error during duplication: {e}")


def export_selected_mix_design(service_container, list_store: Gtk.ListStore, status_bar, context_id, main_window) -> None:
    """Export the selected mix design to a JSON file."""
    try:
        # Find selected item
        selected_id = None
        selected_name = None
        for row in list_store:
            if row[0]:  # If selected
                selected_id = row[6]
                selected_name = row[1]
                break
        
        if not selected_id:
            status_bar.push(context_id, "No item selected")
            return
        
        # File chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Export Mix Design",
            parent=main_window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Save", Gtk.ResponseType.OK
        )
        
        # Set default filename
        dialog.set_current_name(f"{selected_name}.json")
        
        # Add JSON filter
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON files")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            
            # Get mix design and export
            mix_design_service = MixDesignService(service_container.database_service)
            mix_design = mix_design_service.get_by_id(selected_id)
            
            if mix_design:
                # Convert to response format and then to dict
                response_data = mix_design_service.to_response(mix_design)
                export_data = response_data.model_dump()
                
                # Add export metadata
                export_data['_export_info'] = {
                    'exported_at': datetime.now().isoformat(),
                    'vcctl_version': '1.0',
                    'export_type': 'mix_design'
                }
                
                # Write to file
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                status_bar.push(context_id, f"Exported {selected_name} to {filename}")
            else:
                status_bar.push(context_id, "Mix design not found")
        else:
            dialog.destroy()
    
    except Exception as e:
        status_bar.push(context_id, f"Error during export: {e}")


def filter_management_list(original_data: List, list_store: Gtk.ListStore, search_text: str) -> None:
    """Filter the list based on search text."""
    # This is a simplified implementation - in a full version you'd want to store original data
    # and filter from that. For now, this is a placeholder.
    pass


def sort_management_list(list_store: Gtk.ListStore, sort_option: int) -> None:
    """Sort the list based on the selected option."""
    try:
        if sort_option == 0:  # Name (A-Z)
            list_store.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        elif sort_option == 1:  # Name (Z-A)
            list_store.set_sort_column_id(1, Gtk.SortType.DESCENDING)
        elif sort_option == 2:  # Date Created (Newest)
            list_store.set_sort_column_id(3, Gtk.SortType.DESCENDING)
        elif sort_option == 3:  # Date Created (Oldest)
            list_store.set_sort_column_id(3, Gtk.SortType.ASCENDING)
        elif sort_option == 4:  # W/B Ratio (Low to High)
            list_store.set_sort_column_id(4, Gtk.SortType.ASCENDING)
        elif sort_option == 5:  # W/B Ratio (High to Low)
            list_store.set_sort_column_id(4, Gtk.SortType.DESCENDING)
    except Exception as e:
        print(f"Error sorting list: {e}")