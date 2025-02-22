#!/usr/bin/env python
import os
import sys
import time
import shutil
import select
import difflib
import re



# Windows-only: use msvcrt for key detection if available.
if sys.platform.startswith("win"):
    import msvcrt

# Set base directory and master configuration file.
BASE_DIR = os.getcwd()
MASTER_CONFIG = os.path.join(BASE_DIR, "master.txt")

# -----------------------------
# Helper: Pause or Continue
# -----------------------------
def pause_or_continue(timeout=20):
    """
    Displays an under-construction message and waits until either the user
    presses a key or the timeout (in seconds) is reached.
    """
    print("\nSorry, this is under construction for a later update. Keep a lookout!!")
    print("Press Enter to continue or wait 20 seconds...", end="", flush=True)
    start_time = time.time()
    if sys.platform.startswith("win"):
        while True:
            if msvcrt.kbhit():
                msvcrt.getch()
                break
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
    else:
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            sys.stdin.readline()
    print("\nReturning to target system selection...\n")

# -----------------------------
# Helper: Get Expected Systems
# -----------------------------
def get_expected_systems():
    expected = set()
    if not os.path.exists(MASTER_CONFIG):
        return expected
    with open(MASTER_CONFIG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                header = line[1:-1].strip()
                if header == "Working Folder":  # compare case-sensitively
                    continue
                # Store aliases as they appear, without lower-casing.
                aliases = [alias.strip() for alias in header.split("|")]
                for alias in aliases:
                    expected.add(alias)
    return expected

# -----------------------------
# Helper: Get Common Systems
# -----------------------------
def get_common_systems(effective_dir):
    """
    Returns a list of immediate subdirectories from effective_dir that:
      - Have a name exactly matching one of the expected system names (as read from Master.txt).
      - Contain at least one file (ROM file) directly.
      - Contain a "cover art" subfolder with at least one file.
    Appends "All Systems" to the list.
    """
    expected_set = get_expected_systems()
    systems = []
    for d in os.listdir(effective_dir):
        d_path = os.path.join(effective_dir, d)
        if not os.path.isdir(d_path):
            continue
        if d not in expected_set:
            continue
        rom_files = [f for f in os.listdir(d_path) if os.path.isfile(os.path.join(d_path, f))]
        cover_art_path = os.path.join(d_path, "cover art")
        cover_art_files = []
        if os.path.isdir(cover_art_path):
            cover_art_files = [f for f in os.listdir(cover_art_path) if os.path.isfile(os.path.join(cover_art_path, f))]
        if rom_files and cover_art_files:
            systems.append(d)
    systems.append("All Systems")
    return systems

# -----------------------------
# Helper: Get Multiple Selections
# -----------------------------
def get_multiple_selections(options, prompt):
    """
    Displays a list of options and allows the user to select one or more by entering
    comma-separated numbers. Returns a list of selected options, or None if canceled.
    """
    print(prompt)
    for idx, option in enumerate(options, start=1):
        print(f"{idx}. {option}")
    selection = input("Enter your choice(s) separated by commas (or 0 to cancel): ")
    if selection.strip() == "0":
        return None
    tokens = selection.split(',')
    indices = []
    for token in tokens:
        token = token.strip()
        if not token.isdigit():
            print("Invalid input; please enter numbers separated by commas.")
            return None
        indices.append(int(token))
    for i in indices:
        if i < 1 or i > len(options):
            print("Invalid selection number.")
            return None
    if len(options) in indices:
        return options[:-1]
    return [options[i-1] for i in indices]

def remove_parentheses(text):
    return re.sub(r'\([^)]*\)', '', text).strip()

# -----------------------------
# File Sorting Functions
# -----------------------------
def sort_files(effective_dir):
    base_roms_dir = effective_dir
    system_dirs = [d for d in os.listdir(base_roms_dir) if os.path.isdir(os.path.join(base_roms_dir, d))]
    if not system_dirs:
        print("No system directories found in ROMS.")
        return
    for system_dir in system_dirs:
        base_dir = os.path.join(base_roms_dir, system_dir)
        if not os.path.exists(base_dir):
            print(f"Directory {base_dir} does not exist.")
            continue
        excluded_extensions = (".ips", ".bps", ".bin")
        all_files = [f for f in os.listdir(base_dir)
                     if os.path.isfile(os.path.join(base_dir, f)) and not f.lower().endswith(excluded_extensions)]
        def get_folder(filename):
            lower_name = filename.lower()
            if "(e)" in lower_name or "(eur)" in lower_name or "(europe)" in lower_name:
                return "Europe"
            elif "(f)" in lower_name or "(france)" in lower_name:
                return "France"
            elif "(g)" in lower_name or "(germany)" in lower_name:
                return "Germany"
            elif "(i)" in lower_name or "(italy)" in lower_name:
                return "Italy"
            elif "(s)" in lower_name or "(sweden)" in lower_name:
                return "Sweden"
            elif "(spain)" in lower_name:
                return "Spain"
            elif "(netherlands)" in lower_name:
                return "Netherlands"
            elif "(australia)" in lower_name:
                return "Australia"
            elif "(brazil)" in lower_name:
                return "Brazil"
            elif "(asia)" in lower_name:
                return "Asia"
            return None
        category_folders = ["Europe", "France", "Germany", "Italy", "Sweden", "Spain", "Netherlands", "Australia", "Brazil", "Asia", "Translated"]
        for folder in category_folders:
            os.makedirs(os.path.join(base_dir, folder), exist_ok=True)
        for main_file in all_files:
            file_path = os.path.join(base_dir, main_file)
            folder = get_folder(main_file)
            if folder:
                dest_folder = os.path.join(base_dir, folder)
                shutil.move(file_path, os.path.join(dest_folder, main_file))
                print(f"Moved {main_file} to {dest_folder}")
            else:
                print(f"No category found for file: {main_file}")
        for folder in category_folders:
            folder_path = os.path.join(base_dir, folder)
            if os.path.exists(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)
    print("File sorting complete.")

def unsort_files(effective_dir):
    base_roms_dir = effective_dir
    system_dirs = [d for d in os.listdir(base_roms_dir) if os.path.isdir(os.path.join(base_roms_dir, d))]
    if not system_dirs:
        print("No system directories found in ROMS.")
        return
    category_folders = ["Europe", "France", "Germany", "Italy", "Sweden", "Spain", "Netherlands", "Australia", "Brazil", "Asia", "Translated"]
    for system_dir in system_dirs:
        base_dir = os.path.join(base_roms_dir, system_dir)
        if not os.path.exists(base_dir):
            print(f"Directory {base_dir} does not exist.")
            continue
        for folder in category_folders:
            folder_path = os.path.join(base_dir, folder)
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    shutil.move(os.path.join(folder_path, file), os.path.join(base_dir, file))
                    print(f"Moved {file} from {folder_path} back to {base_dir}")
                os.rmdir(folder_path)
    print("File unsorting complete.")

# -----------------------------
# # Working Directory
# -----------------------------
def get_working_folder(target_system):
    mapping = {}
    if os.path.exists(MASTER_CONFIG):
        current_section = None
        with open(MASTER_CONFIG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1].strip()
                    if section.lower() == "working folder":
                        current_section = "working folder"
                    else:
                        current_section = None
                elif current_section == "working folder" and line.startswith("-"):
                    parts = line[1:].split("=", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()  # Preserve case
                        value = parts[1].strip()
                        mapping[key] = value
    else:
        print("Master.txt not found. Defaulting working folder to 'Systems'.")
        mapping = {}

    # Removed special mapping; use the target system name directly.
    key = target_system
    print("DEBUG: Working Folder mapping:", mapping)
    print("DEBUG: Looking for key:", key)
    working_folder = mapping.get(key, "Systems")
    return working_folder\

# -----------------------------
# Run Copy to Drive
# -----------------------------
def run_copy_to_drive(target_system, effective_dir, selected_systems=None):
    """
    Copies files to a selected drive based on paths in Master.txt.
    Fix: Now filters systems based on local ROMS folder instead of the destination drive.
    """

    # Step 1: Select a Drive
    available_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    if not available_drives:
        print("No available drives found. Exiting Copy to Drive...")
        return
    print("\nAvailable drives:")
    for idx, drive in enumerate(available_drives, start=1):
        print(f"{idx}. {drive}")
    drive_choice = input("Enter the number corresponding to the drive to copy to (or 0 to cancel): ").strip()
    if drive_choice == "0":
        print("Cancelling Copy to Drive...")
        return
    try:
        drive_choice = int(drive_choice)
    except ValueError:
        print("Invalid drive selection.")
        return
    if drive_choice < 1 or drive_choice > len(available_drives):
        print("Invalid drive selection.")
        return
    selected_drive = available_drives[drive_choice - 1]

    # Step 2: Parse Master.txt for destination mappings using the selected drive
    mapping = parse_master_drive(selected_drive)

    # Step 3: Filter systems based on **local ROMS directory** (not the destination drive)
    valid_systems = []
    for system in os.listdir(effective_dir):  # List only local systems
        system_path = os.path.join(effective_dir, system)
        if not os.path.isdir(system_path):
            continue  # Skip if it's not a directory

        # Paths to check
        games_path = system_path
        cover_art_path = os.path.join(system_path, "renamed cover art")

        # Check if both exist and have files
        if os.path.exists(games_path) and os.path.exists(cover_art_path):
            if os.listdir(games_path) and os.listdir(cover_art_path):  # Ensure both have files
                valid_systems.append(system)

    valid_systems.sort()  # Ensure consistent order

    if not valid_systems:
        print("\nNo systems found with both games and renamed cover art in ROMS. Exiting Copy to Drive...")
        return

    valid_systems.append("All Systems") if len(valid_systems) > 1 else None

    # Step 4: Select systems for copy
    selected_systems = get_multiple_selections(valid_systems, "\nSelect system(s) for Copy to Drive:")
    
    if selected_systems is None:
        print("Cancelling Copy to Drive...")
        return
    
    if "All Systems" in selected_systems:
        selected_systems = valid_systems[:-1]  # Remove "All Systems" and select all actual systems

    print(f"Running Copy files to Drive for target '{target_system}' on the following systems:")

    def copy_files(src, dest):
        """ Copies files from source to destination. """
        if not os.path.exists(dest):
            os.makedirs(dest)
        for filename in os.listdir(src):
            if target_system == "Nintendo Wii" and filename.lower().endswith(".m3u"):
                print(f"Skipping {filename} (M3U file)")
                continue
            src_file = os.path.join(src, filename)
            dest_file = os.path.join(dest, filename)
            if os.path.isfile(src_file):
                if os.path.exists(dest_file):
                    print(f"✔ {filename} already exists in {dest}; skipping.")
                    continue
                try:
                    shutil.copy(src_file, dest_file)
                    print(f"✔ Copied {filename} → {dest}")
                except Exception as e:
                    print(f"❌ Error copying {filename}: {e}")

    # Step 5: Process each selected system
    for system in selected_systems:
        if system not in mapping:
            print(f"No destination mapping found for system '{system}' in Master.txt.")
            continue

        dest_mapping = mapping[system]
        print(f"  - {system}")
        src_folder = os.path.join(effective_dir, system)

        # Copy game files
        games_key = f"{target_system} games"
        if games_key in dest_mapping:
            dest_games = dest_mapping[games_key]
            copy_files(src_folder, dest_games)

        # Copy renamed cover art
        renamed_key = f"{target_system} renamed cover art"
        renamed_src = os.path.join(src_folder, "renamed cover art")
        if os.path.isdir(renamed_src) and renamed_key in dest_mapping:
            dest_renamed = dest_mapping[renamed_key]
            copy_files(renamed_src, dest_renamed)

    print("✅ Copy operation complete.")
    time.sleep(1)


def run_ftp_transfer(selected_systems, target_system, effective_dir):
    print(f"Running FTP Transfer for target '{target_system}' on the following systems:")
    for system in selected_systems:
        print(f"  - {system}")
    time.sleep(1)

def run_multi_disc_games(selected_systems):
    print("Running M3U creation on the following systems:")
    for system in selected_systems:
        print(f"  - {system}")
    time.sleep(1)

# -----------------------------
# Run Cover Art Matching
# -----------------------------
def run_process_games(target_system, effective_dir, selected_systems=None):
    # Prompt the user to select systems if not provided.
    if selected_systems is None:
        common_systems = get_common_systems(effective_dir)
        selected_systems = get_multiple_selections(common_systems, "\nSelect system(s) for cover art matching:")
        if selected_systems is None:
            print("Cancelling cover art matching...")
            return

    print("Running cover art matching on the following systems:")
    excluded_extensions = (".ips", ".bps", ".bin")
    move_unmatched = input("Move unmatched games to 'unmatched cover art'? (y/n): ").strip().lower() == "y"
    
    for system in selected_systems:
        system_path = os.path.join(effective_dir, system)
        cover_art_folder = os.path.join(system_path, "cover art")
        renamed_folder = os.path.join(system_path, "renamed cover art")
        if not os.path.exists(renamed_folder):
            os.makedirs(renamed_folder, exist_ok=True)
            print(f"Created 'renamed cover art' folder for {system}")
        if move_unmatched:
            unmatched_folder = os.path.join(system_path, "unmatched cover art")
            if not os.path.exists(unmatched_folder):
                os.makedirs(unmatched_folder, exist_ok=True)
                print(f"Created 'unmatched cover art' folder for {system}")
        
        # Get all files in the system folder (ignoring subdirectories)
        all_files = [f for f in os.listdir(system_path) if os.path.isfile(os.path.join(system_path, f))]
        # Define main ROM files (excluding unwanted extensions)
        main_roms = [f for f in all_files if not f.lower().endswith(excluded_extensions)]
        # Get PNG files from the cover art folder.
        png_files = [f for f in os.listdir(cover_art_folder)
                     if f.lower().endswith(".png") and os.path.isfile(os.path.join(cover_art_folder, f))]
        
        for rom in main_roms:
            base_rom = os.path.splitext(rom)[0]
            # Remove any parenthesized parts
            base_rom_clean = remove_parentheses(base_rom).lower()

            best_match = None
            highest_ratio = 0.0
            for png in png_files:
                base_png = os.path.splitext(png)[0]
                base_png_clean = remove_parentheses(base_png).lower()
                ratio = difflib.SequenceMatcher(None, base_rom_clean, base_png_clean).ratio()
                if ratio > highest_ratio:
                    highest_ratio = ratio
                    best_match = png

            if highest_ratio >= 0.75:
                new_name = f"{rom}.png"
                src_path = os.path.join(cover_art_folder, best_match)
                dst_path = os.path.join(renamed_folder, new_name)
                shutil.copy(src_path, dst_path)
                print(f"Matching {rom} -> {new_name} with similarity {highest_ratio:.2f}")
            else:
                print(f"No cover art match found for {rom} (highest similarity: {highest_ratio:.2f})")
                if move_unmatched:
                    unmatched_files = [f for f in all_files if remove_parentheses(os.path.splitext(f)[0]).lower() == base_rom_clean]
                    for af in unmatched_files:
                        src_path = os.path.join(system_path, af)
                        dst_path = os.path.join(unmatched_folder, af)
                        if os.path.exists(src_path):
                            shutil.move(src_path, dst_path)
                            print(f"Moved unmatched file {af} to 'unmatched cover art'")
                        else:
                            print(f"File {src_path} not found, skipping.")


    time.sleep(1)

# -----------------------------
# Restore Unmatched Games
# -----------------------------
def restore_unmatched_games(effective_dir, selected_systems=None):
    print("\nRestoring unmatched games and cleaning up renamed cover art...")

    # Step 1: Get list of systems if not provided
    if selected_systems is None:
        common_systems = get_common_systems(effective_dir)
        selected_systems = get_multiple_selections(common_systems, "\nSelect system(s) to restore unmatched games:")
        if selected_systems is None:
            print("Cancelling restore process...")
            return

    for system in selected_systems:
        system_path = os.path.join(effective_dir, system)
        unmatched_folder = os.path.join(system_path, "unmatched cover art")
        renamed_folder = os.path.join(system_path, "renamed cover art")

        # Step 2: Move files back from unmatched cover art
        if os.path.exists(unmatched_folder):
            for file in os.listdir(unmatched_folder):
                src_path = os.path.join(unmatched_folder, file)
                dest_path = os.path.join(system_path, file)
                try:
                    shutil.move(src_path, dest_path)
                    print(f"✔ Moved {file} back to {system_path}")
                except Exception as e:
                    print(f"❌ Error moving {file}: {e}")

            # Step 3: Delete the now-empty unmatched folder
            try:
                os.rmdir(unmatched_folder)
                print(f"🗑 Deleted empty 'unmatched cover art' folder for {system}")
            except OSError:
                print(f"⚠ Could not delete 'unmatched cover art' for {system} (not empty).")

        # Step 4: Delete renamed cover art folder
        if os.path.exists(renamed_folder):
            try:
                shutil.rmtree(renamed_folder)  # Deletes the folder and all its contents
                print(f"🗑 Deleted 'renamed cover art' folder for {system}")
            except Exception as e:
                print(f"❌ Error deleting 'renamed cover art' for {system}: {e}")

    print("\n✅ Restore process complete!")
    time.sleep(1)


# -----------------------------
# Run Delete Drive Content
# -----------------------------
def run_delete_drive_content(target_system):
    """
    Deletes content on the selected drive based on the paths in master.txt.
    Only shows consoles that have files in both the 'games' and 'renamed cover art' locations.
    """

    # Step 1: Drive Selection
    available_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    if not available_drives:
        print("No available drives found. Exiting Delete Drive Content...")
        return
    print("\nAvailable drives:")
    for idx, drive in enumerate(available_drives, start=1):
        print(f"{idx}. {drive}")
    drive_choice = input("Enter the number corresponding to the drive to delete content from (or 0 to cancel): ").strip()
    if drive_choice == "0":
        print("Cancelling Delete Drive Content...")
        return
    try:
        drive_choice = int(drive_choice)
    except ValueError:
        print("Invalid drive selection.")
        return
    if drive_choice < 1 or drive_choice > len(available_drives):
        print("Invalid drive selection.")
        return
    selected_drive = available_drives[drive_choice - 1]

    # Step 2: Parse Master.txt for destination mappings
    mapping = parse_master_drive(selected_drive)

    # Step 3: Filter consoles with content in both "games" and "renamed cover art"
    prefix = target_system
    valid_systems = []

    for system, dest_mapping in mapping.items():
        games_path = dest_mapping.get(f"{prefix} games", None)
        cover_art_path = dest_mapping.get(f"{prefix} renamed cover art", None)

        if games_path and cover_art_path and os.path.exists(games_path) and os.path.exists(cover_art_path):
            if os.listdir(games_path) and os.listdir(cover_art_path):
                valid_systems.append(system)

    valid_systems.sort()  # <-- Sorting the system names alphabetically

    if not valid_systems:
        print("\nNo systems found with both games and renamed cover art. Exiting Delete Drive Content...")
        return

    valid_systems.append("All Systems") if len(valid_systems) > 1 else None

    # Step 4: Select systems to delete from
    selected_systems = get_multiple_selections(valid_systems, "\nSelect system(s) to delete content from:")
    
    if selected_systems is None:
        print("Deletion cancelled.")
        return
    
    if "All Systems" in selected_systems:
        selected_systems = valid_systems[:-1]  # Remove "All Systems" and select all actual systems

    # Step 5: Confirm Deletion
    confirm_delete = input("⚠ WARNING: Are you sure you want to delete existing files? This action is irreversible! (y/n): ").strip().lower()
    if confirm_delete != "y":
        print("Deletion cancelled.")
        return

    def delete_files(dest):
        """ Delete all contents in the specified destination path. """
        if os.path.exists(dest):
            for file_or_folder in os.listdir(dest):
                full_path = os.path.join(dest, file_or_folder)
                try:
                    if os.path.isfile(full_path) or os.path.islink(full_path):
                        os.remove(full_path)
                        print(f"🗑 Deleted file: {full_path}")
                    elif os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                        print(f"🗑 Deleted folder: {full_path}")
                except Exception as e:
                    print(f"⚠ Error deleting {full_path}: {e}")

    # Step 6: Process each selected system and delete files
    print(f"\n🚀 Deleting content on drive {selected_drive} for selected systems...")

    for system in selected_systems:
        dest_mapping = mapping.get(system, {})
        
        games_path = dest_mapping.get(f"{prefix} games", None)
        cover_art_path = dest_mapping.get(f"{prefix} renamed cover art", None)

        if games_path:
            print(f"🧹 Deleting files in: {games_path}...")
            delete_files(games_path)

        if cover_art_path:
            print(f"🧹 Deleting files in: {cover_art_path}...")
            delete_files(cover_art_path)

    print("✅ Drive cleanup complete.")

# -----------------------------
# Parse Master Function
# -----------------------------
def parse_master_drive(selected_drive):
    mapping = {}
    if not os.path.exists(MASTER_CONFIG):
        return mapping
    current_aliases = []
    with open(MASTER_CONFIG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                header = line[1:-1].strip()
                if header.lower() == "working folder":
                    current_aliases = []
                    continue
                current_aliases = [alias.strip() for alias in header.split("|")]
                mapping_for_alias = {}
                for alias in current_aliases:
                    mapping[alias] = mapping_for_alias
            elif current_aliases and line.startswith("-"):
                parts = line[1:].split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if selected_drive is None:
                        selected_drive = ""
                    value = value.replace("drive:", selected_drive)
                    for alias in current_aliases:
                        mapping[alias][key] = value
    return mapping

# -----------------------------
# Main Menu
# -----------------------------
def main():
    while True:
        print("\nWhich system are we making this for?")
        print("1. Raspberry Pi")
        print("2. Nintendo Wii")
        print("3. Microsoft XBOX")
        target_choice = input("Enter your choice (0 will exit): ").strip()
        target_map = {
            "1": "rpi",
            "2": "wii",
            "3": "xbox",
        }
        if target_choice == "0":
            print("Exiting program...")
            return
        if target_choice not in target_map:
            print("Invalid selection. Try again.")
            continue
        
        target_system = target_map[target_choice]
        print(f"Using destination mappings for '{target_system}'.")
        effective_dir = os.path.join(BASE_DIR, get_working_folder(target_system))

        if target_choice == "2":
            while True:
                print(f"\nOperations Menu for {target_system}:")
                print("1. Match cover art to games")
                print("2. Undo matching of cover art")
                print("3. Copy files to drive")
                print("4. Delete content from drive")
                print("5. Sort files")
                print("6. Unsort files")
                op_choice = input("Enter your selection (or 0 to return): ").strip()

                if op_choice == "0":
                    break
                elif op_choice == "1":
                    run_process_games(target_system, effective_dir)
                elif op_choice == "2":
                    restore_unmatched_games(effective_dir)
                elif op_choice == "3":
                    run_copy_to_drive(target_system, effective_dir)
                elif op_choice == "4":
                    run_delete_drive_content(target_system)
                elif op_choice == "5":
                    sort_files(effective_dir)
                elif op_choice == "6":
                    unsort_files(effective_dir)
                else:
                    print("Invalid selection. Try again.")

                print("\nOperation Complete!! Returning to Operations Menu...")
                time.sleep(2)
        else:
            pause_or_continue()

if __name__ == "__main__":
    main()
