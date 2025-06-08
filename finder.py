"""
Module for searching files in the file system
"""

from pathlib import Path
from typing import List
from logger import get_logger

# Supported image file extensions
IMAGE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.bmp',
    '.gif',
    '.tiff',
    '.tif',
    '.webp'}


def find_all_files(directory: str) -> List[Path]:
    """
    Finds all files in the specified folder recursively

    Args:
        directory: Path to the folder to search

    Returns:
        List of paths to found files
    """
    logger = get_logger()

    try:
        path = Path(directory)
        if not path.exists():
            logger.error(f"Directory does not exist: {directory}")
            return []

        if not path.is_dir():
            logger.error(f"Specified path is not a directory: {directory}")
            return []

        # Recursively find all files in the folder and subfolders
        files = [f for f in path.rglob('*') if f.is_file()]
        return files

    except Exception as e:
        logger.error(f"Error while searching files in {directory}: {e}")
        return []


def find_image_files(directory: str) -> List[Path]:
    """
    Finds all image files in the specified folder recursively

    Args:
        directory: Path to the folder to search

    Returns:
        List of paths to found image files
    """
    all_files = find_all_files(directory)

    # Filter only images by extension (case-insensitive)
    image_files = [
        f for f in all_files
        if f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    return image_files
