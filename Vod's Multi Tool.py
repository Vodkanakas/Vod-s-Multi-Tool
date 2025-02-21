#!/usr/bin/env python
import os
import sys
import time
import shutil
import select


# Windows-only: use msvcrt for key detection if available.
if sys.platform.startswith("win"):
    import msvcrt

# Set base directory and master configuration file.
BASE_DIR = os.getcwd()
MASTER_CONFIG = os.path.join(BASE_DIR, "master.txt")

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
    
def get_working_folder(target_system):
    """
    Reads the [Working Folder] section from Master.txt and returns the folder name
    associated with the given target system.
    
    Expected Master.txt (for example):
    
    [Working Folder]
    - wii = ROMS
    - rpi = roms
    - xbox = XBOX_ROMS
    - xbox 360 = XBOX360_ROMS
    
    Uses a special mapping so that e.g. "Raspberry Pi" returns the key "rpi".
    """
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
    
    # Special mapping for target system names.
    special_keys = {
        "Raspberry Pi": "rpi",
        "Nintendo Wii": "wii",
        "Microsoft XBOX": "xbox",
        "Microsoft XBOX 360": "xbox 360"
    }
    key = special_keys.get(target_system, target_system.split()[-1])
    print("DEBUG: Working Folder mapping:", mapping)
    print("DEBUG: Looking for key:", key)
    working_folder = mapping.get(key, "Systems")
    return working_folder

# -----------------------------
# Run Copy to Drive
# -----------------------------
def run_copy_to_drive(target_system, effective_dir, selected_systems=None):
    # Step 1: Drive Selection
    available_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    if not available_drives:
        print("No available drives found. Exiting Copy to Drive...")
        return
    print("Available drives:")
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
    
    # Step 2: Parse Master.txt for destination mappings using the selected drive.
    mapping = parse_master_drive(selected_drive)
    
    # Step 3: Prompt for system selection if not provided.
    if selected_systems is None:
        common_systems = get_common_systems(effective_dir)
        selected_systems = get_multiple_selections(common_systems, "\nSelect system(s) for Copy to Drive:")
        if selected_systems is None:
            print("Cancelling Copy to Drive...")
            return

    print(f"Running Copy files to Drive for target '{target_system}' on the following systems:")
    target_prefix_map = {
        "Raspberry Pi": "rpi",
        "Nintendo Wii": "wii",
        "Microsoft XBOX": "xbox",
        "Microsoft XBOX 360": "xbox 360"
    }
    prefix = target_prefix_map.get(target_system, target_system.split()[-1])
    
    def copy_files(src, dest):
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
    
    for system in selected_systems:
        system_key = system
        if system_key not in mapping:
            print(f"No destination mapping found for system '{system}' in Master.txt.")
            continue
        dest_mapping = mapping[system_key]
        print(f"  - {system}")
        src_folder = os.path.join(effective_dir, system)
        
        # Regular ROM files: use key "<prefix> games"
        games_key = f"{prefix} games"
        if games_key not in dest_mapping:
            print(f"No 'games' destination mapping found for system '{system}' using key '{games_key}'.")
        else:
            dest_games = dest_mapping[games_key]
            copy_files(src_folder, dest_games)
        
        # Process Multi Disc folder.
        multi_disc_folder = os.path.join(effective_dir, "Multi Disc", system)
        if os.path.isdir(multi_disc_folder):
            if target_system == "Raspberry Pi":
                multi_disc_key = "rpi multi disc"
            else:
                multi_disc_key = games_key
            if multi_disc_key in dest_mapping:
                dest_multi = dest_mapping[multi_disc_key]
                copy_files(multi_disc_folder, dest_multi)
            else:
                print(f"No destination mapping for Multi Disc files for system '{system}' using key '{multi_disc_key}'.")
        
        # Optionally, process "renamed cover art" if present.
        renamed_key = f"{prefix} renamed cover art"
        renamed_src = os.path.join(src_folder, "renamed cover art")
        if os.path.isdir(renamed_src) and renamed_key in dest_mapping:
            copy_files(renamed_src, dest_mapping[renamed_key])
        
        # Optionally, process "bios" if present.
        bios_key = f"{prefix} bios"
        bios_src = os.path.join(src_folder, "bios")
        if os.path.isdir(bios_src) and bios_key in dest_mapping:
            copy_files(bios_src, dest_mapping[bios_key])
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
# Run FTP Transfer
# -----------------------------
def run_ftp_transfer(target_system):
    ip_address = input("Enter the IP address of the FTP device: ").strip()
    print(f"Starting FTP Transfer to {ip_address} for {target_system}...")
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
            matched = False
            for png in png_files:
                if base_rom in os.path.splitext(png)[0]:
                    new_name = f"{rom}.png"
                    src_path = os.path.join(cover_art_folder, png)
                    dst_path = os.path.join(renamed_folder, new_name)
                    shutil.copy(src_path, dst_path)
                    print(f"Matching {rom} -> {new_name}")
                    matched = True
                    break
            if not matched:
                print(f"No cover art match found for {rom}")
                if move_unmatched:
                    associated_files = [f for f in all_files if os.path.splitext(f)[0] == base_rom]
                    for af in associated_files:
                        src_path = os.path.join(system_path, af)
                        dst_path = os.path.join(unmatched_folder, af)
                        shutil.move(src_path, dst_path)
                        print(f"Moved unmatched file {af} to 'unmatched cover art'")
    time.sleep(1)


# -----------------------------
# Parse Master Function
# -----------------------------
def parse_master_drive(selected_drive):
    """
    Reads Master.txt (ignoring the [Working Folder] section) and returns a mapping
    dictionary that maps each system alias (exactly as written) to a dictionary of destination
    paths. In the mapping values, the string "drive:" is replaced with selected_drive.
    
    For example, if Master.txt contains:
    
    [Playstation|PS1|PSX]
    - wii bios = drive:\wiisxrx\bios
    - wii games = drive:\wiisxrx\isos
    - wii renamed cover art = drive:\wiiflow\boxcovers\Playstation
    
    and if selected_drive is "D:\", then "drive:" is replaced with "D:\".
    """
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
        print("4. Microsoft XBOX 360")
        target_choice = input("Enter your choice (0 will exit): ").strip()
        target_map = {
            "1": "Raspberry Pi",
            "2": "Nintendo Wii",
            "3": "Microsoft XBOX",
            "4": "Microsoft XBOX 360"
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
                print("2. Copy files to drive")
                op_choice = input("Enter your selection (or 0 to return): ").strip()
                if op_choice == "0":
                    break
                elif op_choice == "1":
                    run_process_games(target_system, effective_dir)
                elif op_choice == "2":
                    run_copy_to_drive(target_system, effective_dir)

                else:
                    print("Invalid selection. Try again.")
                input("\nPress Enter to return to the operations menu...")
        else:
            pause_or_continue()

        input("\nPress Enter to return to the target system selection...")

if __name__ == "__main__":
    main()
