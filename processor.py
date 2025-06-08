"""
Module for image processing
"""

from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image
import imagehash
from tqdm import tqdm
from logger import get_logger


def load_image(file_path: Path) -> Optional[Image.Image]:
    """
    Loads an image from a file

    Args:
        file_path: Path to the image file

    Returns:
        PIL Image object or None if an error occurs
    """
    logger = get_logger()

    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        if not file_path.is_file():
            logger.warning(f"Specified path is not a file: {file_path}")
            return None

        # Load the image using PIL
        image = Image.open(file_path)

        # Verify that this is indeed an image
        image.verify()

        # Reload after verify() (verify() makes the object unusable)
        image = Image.open(file_path)

        return image

    except (IOError, OSError) as e:
        logger.warning(f"Error loading image {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        return None


def convert_to_grayscale(image: Image.Image) -> Image.Image:
    """
    Converts an image to grayscale

    Args:
        image: PIL Image object

    Returns:
        Grayscale image in 'L' mode
    """
    return image.convert('L')


def resize_image(image: Image.Image, size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """
    Resizes the image to a standard size

    Args:
        image: PIL Image object
        size: Target size (width, height)

    Returns:
        Image resized to the specified size without adding a background
    """
    # Simply resize without preserving aspect ratio for more accurate hashing
    return image.resize(size, Image.Resampling.LANCZOS)


def calculate_hash(image: Image.Image) -> imagehash.ImageHash:
    """
    Calculates the hash of an image

    Args:
        image: PIL Image object

    Returns:
        Perceptual hash of the image (more robust to geometric transformations)
    """
    # Use perceptual hash instead of difference hash for better accuracy
    return imagehash.phash(image, hash_size=16)


def process_single_image(file_path: Path) -> Optional[imagehash.ImageHash]:
    """
    Processing pipeline for a single image

    Args:
        file_path: Path to the image file

    Returns:
        Image hash or None if processing fails
    """
    logger = get_logger()

    try:
        # Load the image
        image = load_image(file_path)
        if image is None:
            return None

        # Convert to grayscale
        gray_image = convert_to_grayscale(image)

        # Resize to a smaller standard size without adding a background
        resized_image = resize_image(gray_image, (256, 256))

        # Calculate improved hash
        image_hash = calculate_hash(resized_image)

        return image_hash

    except Exception as e:
        logger.error(f"Error processing image {file_path}: {e}")
        return None


def process_images(file_paths: List[Path]
                   ) -> List[Tuple[Path, imagehash.ImageHash]]:
    """
    Processes a list of images with progress display

    Args:
        file_paths: List of image file paths

    Returns:
        List of tuples (file_path, hash) for successfully processed images
    """
    results = []

    # Use tqdm to display progress
    for file_path in tqdm(
            file_paths, desc="Processing images", unit="file"):
        image_hash = process_single_image(file_path)
        if image_hash is not None:
            results.append((file_path, image_hash))
        # Skip files that could not be processed

    return results
