#!/usr/bin/env python3
"""
Repository cleanup script for VCCTL-GTK project
Removes temporary files, test scripts, and obsolete documentation
Based on assessment with user feedback incorporated
"""

import os
import shutil
import glob
import subprocess
import sys
from pathlib import Path

def main():
    """Main cleanup function"""
    
    # Get the script directory (should be run from root)
    root_dir = Path.cwd()
    print(f"Cleaning up repository at: {root_dir}")
    
    cleanup_stats = {
        'files_removed': 0,
        'dirs_removed': 0,
        'git_files_removed': 0,
        'bytes_freed': 0
    }
    
    # 1. REMOVE LOG FILES
    print("\n=== Removing log files ===")
    log_files = [
        "aggregate_dialog_test.log",
        "all_tabs_test.log", 
        "app_test.log",
        "complete_simulation_test.log",
        "complete_test.log",
        "derby.log",
        "dblook.log", 
        "disrealnew.log",
        "final_complete_test.log",
        "fixed_aggregate_dialog_test.log",
        "hydration_test.log",
        "microstructure_test.log",
        "test_with_all_files.log",
        "derby_export.log",
        "migration_log.txt"
    ]
    
    for log_file in log_files:
        remove_file(root_dir / log_file, cleanup_stats)
    
    # 2. REMOVE TEST/DEBUG SCRIPTS (excluding migrate_*.py)
    print("\n=== Removing test and debug scripts ===")
    
    # Get all python files and filter out the ones to keep
    all_py_files = glob.glob("*.py")
    
    # Files to keep (not remove)
    keep_files = {
        "setup.py",
        "pytest.ini"  # Actually not .py but in same category
    }
    
    # Keep all migrate_*.py files
    migrate_files = set(glob.glob("migrate_*.py"))
    
    for py_file in all_py_files:
        py_path = Path(py_file)
        
        # Skip files we want to keep
        if py_file in keep_files:
            continue
            
        # Skip migrate scripts
        if py_file in migrate_files:
            continue
            
        # Skip main application files
        if py_file in ["setup.py"]:
            continue
            
        # Remove test, debug, analyze, apply, batch, etc. scripts
        prefixes_to_remove = [
            "analyze_", "apply_", "batch_", "calculate_", "carbon_",
            "check_", "complete_", "debug_", "demo_", "end_to_end_demo",
            "extract_", "fix_", "generate_", "test_", "run_tests", 
            "run_integration_tests", "icon_", "interactive_", 
            "microstructure_temp", "quick_", "reset_", "simple_",
            "simulate_", "update_", "initialize_", "integrate_",
            "finalize_"
        ]
        
        should_remove = any(py_file.startswith(prefix) for prefix in prefixes_to_remove)
        
        if should_remove:
            remove_file(root_dir / py_file, cleanup_stats)
    
    # 3. REMOVE OBSOLETE DOCUMENTATION
    print("\n=== Removing obsolete documentation ===")
    obsolete_docs = [
        "AGGREGATE_FIX_COMPLETE.md",
        "ALKALI_DATA_FILES_INTEGRATION_COMPLETE.md", 
        "HYDRATION_INTEGRATION_STATUS.md",
        "HelpMigrateAndPythonEnvironment.md",
        "ICON_INTEGRATION_SUMMARY.md",
        "MCP_INTEGRATION_COMPLETE.md",
        "MIGRATION_GUIDE.md",
        "OPERATIONS_PANEL_STATUS_SUMMARY.md",
        "OPERATIONS_PROGRESS_TRACKING_FIX.md",
        "PSD_IMPORT_STATUS.md",
        "PSD_UPDATE_COMPLETE.md",
        "PYVISTA_DATA_ORDERING_FIX.md", 
        "UI_POLISH_FIXES_COMPLETE.md",
        "UNIFIED_PSD_IMPLEMENTATION_SUMMARY.md",
        "UNIFIED_PSD_INTEGRATION_COMPLETE.md",
        "aggregate_migration_fix_report.md",
        "conversation_reference.md",
        "correlation_files_report.txt",
        "icon_migration_report.txt",
        "icon_suggestions.md",
        "longjmp_workaround_explanation.md",
        "toDo_2025-08-19.md"
    ]
    
    for doc_file in obsolete_docs:
        remove_file(root_dir / doc_file, cleanup_stats)
    
    # 4. REMOVE TEMPORARY FILES
    print("\n=== Removing temporary files ===")
    temp_files = [
        "console_output.txt",
        "parameters.csv",
        "psdtest.csv",
        "vcctl.db",  # Empty duplicate in root
        "materials.db",
        "disrealnew_clean.c",
        "OneVoxelBias.java",
        "disrealnew_input_after_parameters.txt",
        "genmic_input_air_0.0.txt",
        "genmic_input_air_0.05.txt",
        "HydrationSim_E2ETest_20250812_165252_extended_parameters.csv",
        "claude_code_mcp_config.json",
        "ࡥm_"  # This seems to be a corrupted filename
    ]
    
    # Add test CSV files
    test_csv_files = glob.glob("test_*.csv") + glob.glob("test_*.txt")
    temp_files.extend(test_csv_files)
    
    for temp_file in temp_files:
        remove_file(root_dir / temp_file, cleanup_stats)
    
    # 5. REMOVE ARCHIVE FILES
    print("\n=== Removing archive files ===")
    archive_files = glob.glob("*.tar.gz")
    for archive_file in archive_files:
        remove_file(root_dir / archive_file, cleanup_stats)
    
    # 6. REMOVE OBSOLETE DIRECTORIES
    print("\n=== Removing obsolete directories ===")
    obsolete_dirs = [
        ".ipynb_checkpoints",
        "ClaudeTest", 
        "FirstMortar",
        "derby_export",
        "derby_export_fixed", 
        "derby_original_database",
        "db-derby-10.16.1.1-bin",
        "db-derby-10.5.3.0-bin",
        "db-derby-10.6.2.1-bin",
        "microstructure_metadata",
        "scratch",
        "tests_mcp",
        "venv",  # Old virtual environment
        "vcctl-gtk-env",  # Old virtual environment
        "node_modules"  # If exists and not needed
    ]
    
    for dir_name in obsolete_dirs:
        remove_directory(root_dir / dir_name, cleanup_stats)
    
    # 7. SUMMARY
    print(f"\n=== Cleanup Summary ===")
    print(f"Regular files removed: {cleanup_stats['files_removed']}")
    print(f"Git-tracked files removed: {cleanup_stats['git_files_removed']}")
    print(f"Directories removed: {cleanup_stats['dirs_removed']}")
    print(f"Approximate space freed: {cleanup_stats['bytes_freed'] / (1024*1024):.1f} MB")
    print("\nCleanup completed!")
    
    if cleanup_stats['git_files_removed'] > 0:
        print(f"\nIMPORTANT: {cleanup_stats['git_files_removed']} git-tracked files were removed.")
        print("These changes are staged for the next commit.")
        print("Run 'git status' to see the staged deletions.")
        print("Run 'git commit -m \"Remove temporary and obsolete files\"' to commit the changes.")
    
    # 8. SHOW WHAT'S LEFT
    print(f"\n=== Remaining files in root directory ===")
    remaining_files = []
    for item in sorted(root_dir.iterdir()):
        if item.is_file():
            remaining_files.append(item.name)
        else:
            remaining_files.append(f"{item.name}/")
    
    for i, item in enumerate(remaining_files, 1):
        print(f"{i:2d}. {item}")

def is_git_tracked(file_path):
    """Check if a file is tracked by git"""
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--', str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent if file_path.is_file() else file_path
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False

def remove_file(file_path, stats):
    """Safely remove a file and update statistics"""
    try:
        if not file_path.exists():
            print(f"  Not found: {file_path.name}")
            return
            
        if not file_path.is_file():
            print(f"  Not a file: {file_path.name}")
            return
            
        size = file_path.stat().st_size
        
        # Check if file is git-tracked
        if is_git_tracked(file_path):
            # Use git rm to remove from repository
            result = subprocess.run(
                ['git', 'rm', str(file_path)],
                capture_output=True,
                text=True,
                cwd=file_path.parent
            )
            if result.returncode == 0:
                stats['git_files_removed'] += 1
                stats['bytes_freed'] += size
                print(f"  Git removed: {file_path.name} ({size:,} bytes)")
            else:
                print(f"  Git rm failed for {file_path.name}: {result.stderr.strip()}")
        else:
            # Regular file deletion for untracked files
            file_path.unlink()
            stats['files_removed'] += 1
            stats['bytes_freed'] += size
            print(f"  Removed file: {file_path.name} ({size:,} bytes)")
            
    except Exception as e:
        print(f"  Error removing {file_path.name}: {e}")

def remove_directory(dir_path, stats):
    """Safely remove a directory and update statistics"""
    try:
        if not dir_path.exists():
            print(f"  Not found: {dir_path.name}/")
            return
            
        if not dir_path.is_dir():
            print(f"  Not a directory: {dir_path.name}")
            return
            
        # Calculate size before removal
        total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
        
        # Check if directory contains git-tracked files
        has_git_files = False
        try:
            result = subprocess.run(
                ['git', 'ls-files', str(dir_path)],
                capture_output=True,
                text=True,
                cwd=dir_path.parent
            )
            has_git_files = result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            has_git_files = False
        
        if has_git_files:
            # Use git rm for directories with tracked files
            result = subprocess.run(
                ['git', 'rm', '-r', str(dir_path)],
                capture_output=True,
                text=True,
                cwd=dir_path.parent
            )
            if result.returncode == 0:
                stats['git_files_removed'] += 1
                stats['bytes_freed'] += total_size
                print(f"  Git removed directory: {dir_path.name}/ ({total_size:,} bytes)")
            else:
                print(f"  Git rm failed for {dir_path.name}/: {result.stderr.strip()}")
        else:
            # Regular directory deletion for untracked directories
            shutil.rmtree(dir_path)
            stats['dirs_removed'] += 1
            stats['bytes_freed'] += total_size
            print(f"  Removed directory: {dir_path.name}/ ({total_size:,} bytes)")
            
    except Exception as e:
        print(f"  Error removing {dir_path.name}/: {e}")

if __name__ == "__main__":
    # Confirm before running
    print("VCCTL Repository Cleanup Script")
    print("=" * 40)
    print("This will remove temporary files, test scripts, and obsolete documentation.")
    print("Git-tracked files will be removed using 'git rm' and staged for commit.")
    print("Untracked files will be deleted directly.")
    print("")
    print("The following will be PRESERVED:")
    print("  - migrate_*.py scripts")
    print("  - alkalichar.dat, alkaliflyash.dat, slagchar.dat")
    print("  - vcctl-clean-env/ (active virtual environment)")
    print("  - src/data/database/vcctl.db* (active database files)")
    print("")
    
    # Check for --yes flag to skip confirmation
    if len(sys.argv) > 1 and sys.argv[1] == '--yes':
        print("Auto-confirming cleanup due to --yes flag")
        main()
    else:
        response = input("Continue with cleanup? (y/N): ").strip().lower()
        if response == 'y':
            main()
        else:
            print("Cleanup cancelled.")