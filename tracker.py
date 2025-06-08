"""
Module for tracking saved files and managing the deletion list
"""

import json
from pathlib import Path
from typing import List
import config
from logger import get_logger


def save_file_mapping(groups: List[List[Path]], output_dir: str,
                      group_folders: List[Path]) -> None:
    """
    Saves information about which files were copied where

    Args:
        groups: List of groups with original file paths
        output_dir: Path to the results folder
        group_folders: List of created group folders
    """
    logger = get_logger()

    file_mapping = {}

    for group_index, group_paths in enumerate(groups):
        group_folder = group_folders[group_index]

        for file_path in group_paths:
            if file_path.exists():
                # Generate the expected file name (same logic as in saver)
                safe_filename = _path_to_filename(file_path)
                destination = group_folder / safe_filename

                # Handle possible duplicate names
                counter = 1
                original_dest = destination
                while str(destination) in file_mapping.values():
                    stem = original_dest.stem
                    suffix = original_dest.suffix
                    destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                    counter += 1

                file_mapping[str(file_path)] = str(destination)

    # Save the mapping to a file
    info_file = Path(config.INFO_FILE)
    info_file.parent.mkdir(parents=True, exist_ok=True)

    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(file_mapping, f, ensure_ascii=False, indent=2)

    logger.info(f"Information about saved files written to {info_file}")
    logger.info(f"Total records in mapping: {len(file_mapping)}")


def _path_to_filename(file_path: Path) -> str:
    """
    Converts the full file path to a safe file name
    Copy of the function from saver for consistency
    """
    import re

    path_str = str(file_path)
    safe_name = re.sub(r'[^\w\.-]', '_', path_str)
    safe_name = re.sub(r'_{2,}', '_', safe_name)
    safe_name = safe_name.strip('_')

    if not safe_name or len(safe_name) > 200:
        safe_name = file_path.name
        if not safe_name:
            safe_name = "unknown_file"

    return safe_name


def find_files_to_delete() -> None:
    """
    Analyzes OUTPUT_DIR and INFO_FILE, finds deleted files,
    and writes their original paths to TO_DELETE_FILE
    """
    logger = get_logger()

    info_file = Path(config.INFO_FILE)
    output_dir = Path(config.OUTPUT_DIR)
    to_delete_file = Path(config.TO_DELETE_FILE)

    if not info_file.exists():
        logger.warning(f"Info file {info_file} not found")
        return

    if not output_dir.exists():
        logger.warning(f"Results folder {output_dir} not found")
        return

    # Load information about saved files
    try:
        with open(info_file, 'r', encoding='utf-8') as f:
            file_mapping = json.load(f)
    except Exception as e:
        logger.error(f"Error reading {info_file}: {e}")
        return

    logger.info(f"Loaded mapping from {info_file} ({len(file_mapping)} records)")

    # Get the list of existing files in OUTPUT_DIR
    existing_files = set()
    for file_path in output_dir.rglob('*'):
        if file_path.is_file():
            existing_files.add(str(file_path))

    logger.info(f"Found files in {output_dir}: {len(existing_files)}")

    # Find files that were in the mapping but no longer exist
    files_to_delete = []
    for original_path, saved_path in file_mapping.items():
        if saved_path not in existing_files:
            files_to_delete.append(original_path)
            logger.info(f"File deleted from OUTPUT_DIR: {saved_path} -> adding to delete: {original_path}")

    if not files_to_delete:
        logger.info("No files to delete")
        return

    # Write paths for deletion
    to_delete_file.parent.mkdir(parents=True, exist_ok=True)

    with open(to_delete_file, 'w', encoding='utf-8') as f:
        for file_path in files_to_delete:
            f.write(f"{file_path}\n")

    logger.info(f"Wrote {len(files_to_delete)} paths for deletion to {to_delete_file}")

    # Output statistics
    logger.info("=== STATISTICS ===")
    logger.info(f"Total files saved: {len(file_mapping)}")
    logger.info(f"Remaining in OUTPUT_DIR: {len(existing_files)}")
    logger.info(f"Marked for deletion: {len(files_to_delete)}")


def cleanup_deleted_files() -> None:
    """
    Deletes files listed in TO_DELETE_FILE
    """
    logger = get_logger()

    to_delete_file = Path(config.TO_DELETE_FILE)

    if not to_delete_file.exists():
        logger.warning(f"File {to_delete_file} not found")
        return

    deleted_count = 0
    error_count = 0

    with open(to_delete_file, 'r', encoding='utf-8') as f:
        for line in f:
            file_path = Path(line.strip())
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"Deleted file: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
                    error_count += 1
            else:
                logger.warning(f"File does not exist anymore: {file_path}")

    logger.info("=== DELETION RESULT ===")
    logger.info(f"Successfully deleted: {deleted_count}")
    logger.info(f"Errors during deletion: {error_count}")
