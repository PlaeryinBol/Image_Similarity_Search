"""
Module for saving the results of image grouping
"""

import shutil
import re
from pathlib import Path
from typing import List
from logger import get_logger
from tracker import save_file_mapping


def create_output_folders(output_dir: str, num_groups: int) -> List[Path]:
    """
    Creates a folder structure for saving results

    Args:
        output_dir: Path to the results folder
        num_groups: Number of groups to create folders for

    Returns:
        List of paths to created folders
    """
    logger = get_logger()
    output_path = Path(output_dir)

    # If the results folder exists, clear it
    if output_path.exists():
        logger.info(f"Clearing existing results folder: {output_path}")
        shutil.rmtree(output_path)

    # Create the main results folder
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created results folder: {output_path}")

    # Create numbered subfolders for each group
    created_folders = []
    for i in range(1, num_groups + 1):
        group_folder = output_path / str(i)
        group_folder.mkdir(exist_ok=True)
        created_folders.append(group_folder)
        logger.info(f"Created group folder {i}: {group_folder}")

    return created_folders


def path_to_filename(file_path: Path) -> str:
    """
    Converts the full file path to a safe file name

    Args:
        file_path: Full path to the file

    Returns:
        Safe file name for use in the file system
    """
    # Get the full path as a string
    path_str = str(file_path)

    # Replace slashes and other special characters with underscores
    # Keep only letters, digits, dots, dashes, and underscores
    safe_name = re.sub(r'[^\w\.-]', '_', path_str)

    # Remove repeated underscores
    safe_name = re.sub(r'_{2,}', '_', safe_name)

    # Remove underscores at the beginning and end
    safe_name = safe_name.strip('_')

    # If the name is empty or too long, create an alternative
    if not safe_name or len(safe_name) > 200:
        # Use only the file name and extension
        safe_name = file_path.name
        if not safe_name:
            safe_name = "unknown_file"

    return safe_name


def save_groups(groups: List[List[Path]], output_dir: str) -> None:
    """
    Copies group files to corresponding folders with renaming

    Args:
        groups: List of groups, where each group is a list of image paths
        output_dir: Path to the folder for saving results
    """
    logger = get_logger()

    if not groups:
        logger.warning("No groups to save")
        return

    # Create folders for results
    output_folders = create_output_folders(output_dir, len(groups))

    total_files_copied = 0

    # Copy files of each group to the corresponding folder
    for group_index, group_paths in enumerate(groups):
        group_folder = output_folders[group_index]
        group_num = group_index + 1

        logger.info(f"Saving group {group_num} ({len(group_paths)} files):")

        for file_path in group_paths:
            try:
                if not file_path.exists():
                    logger.warning(f"  File not found: {file_path}")
                    continue

                # Generate a safe file name
                safe_filename = path_to_filename(file_path)

                # Create the destination path
                destination = group_folder / safe_filename

                # If a file with this name already exists, add a number
                counter = 1
                original_dest = destination
                while destination.exists():
                    stem = original_dest.stem
                    suffix = original_dest.suffix
                    destination = original_dest.parent / \
                        f"{stem}_{counter}{suffix}"
                    counter += 1

                # Copy the file
                shutil.copy2(file_path, destination)
                logger.info(f"  {file_path.name} -> {destination.name}")
                total_files_copied += 1

            except Exception as e:
                logger.error(f"  Error copying {file_path}: {e}")

    logger.info(f"Total files copied: {total_files_copied}")
    logger.info(f"Results saved in: {output_dir}")

    # Save information about which files were copied where
    save_file_mapping(groups, output_dir, output_folders)
