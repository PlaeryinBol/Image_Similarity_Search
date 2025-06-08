#!/usr/bin/env python3
"""
Tool for finding similar images and removing duplicates
"""

import argparse

import config
from finder import find_image_files
from tracker import cleanup_deleted_files, find_files_to_delete
from processor import process_single_image
from logger import get_logger, setup_logger
from saver import save_groups
from similarity import find_similar_pairs, group_similar_images


def find_duplicates():
    """Main function for finding duplicates"""
    logger = get_logger()

    try:
        logger.info("=== Duplicate Image Finder ===")

        # Step 1: Read configuration
        logger.info("📋 Reading configuration...")
        input_dir = config.INPUT_DIR
        output_dir = config.OUTPUT_DIR
        threshold = config.THRESHOLD

        logger.info(f"  Input folder: {input_dir}")
        logger.info(f"  Output folder: {output_dir}")
        logger.info(f"  Similarity threshold: {threshold}")

        # Step 2: Search for image files
        logger.info("🔍 Searching for image files...")
        image_files = find_image_files(input_dir)

        if not image_files:
            logger.error("❌ No images found!")
            return

        logger.info(f"  Images found: {len(image_files)}")

        # Step 3: Process images (using improved algorithm)
        logger.info("🖼️  Processing images...")

        # Use improved processing for more accurate hashing
        image_data = []
        from tqdm import tqdm
        for file_path in tqdm(image_files, desc="Processing images", unit="file"):
            image_hash = process_single_image(file_path)
            if image_hash is not None:
                image_data.append((file_path, image_hash))

        if not image_data:
            logger.error("❌ Failed to process any images!")
            return

        logger.info(f"  Successfully processed: {len(image_data)} of {len(image_files)}")

        # Step 4: Find similar pairs
        logger.info("🔗 Finding similar images...")
        similar_pairs = find_similar_pairs(image_data, threshold)

        if not similar_pairs:
            logger.info("✅ No similar images found!")
            return

        logger.info(f"  Similar pairs found: {len(similar_pairs)}")

        # Step 5: Group similar images
        logger.info("📁 Grouping similar images...")
        groups = group_similar_images(similar_pairs)

        if not groups:
            logger.error("❌ Failed to create groups!")
            return

        logger.info(f"  Groups created: {len(groups)}")
        for i, group in enumerate(groups, 1):
            logger.info(f"    Group {i}: {len(group)} images")

        # Step 6: Save results
        logger.info("💾 Saving results...")
        save_groups(groups, output_dir)

        logger.info("✅ Processing completed successfully!")

    except KeyboardInterrupt:
        logger.warning("⏹️  Processing interrupted by user")
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")
        return


def main():
    """Main function with command-line argument handling"""
    # Set up logging before anything else
    setup_logger()
    logger = get_logger()

    parser = argparse.ArgumentParser(description="Tool for finding similar images")
    parser.add_argument(
        '--action',
        choices=['find', 'check-deleted', 'cleanup'],
        default='find',
        help='Action: find (find duplicates), check-deleted (find files to delete), cleanup (delete files)'
    )

    args = parser.parse_args()

    try:
        if args.action == 'find':
            find_duplicates()
        elif args.action == 'check-deleted':
            logger.info("🔍 Searching for files to delete...")
            find_files_to_delete()
        elif args.action == 'cleanup':
            logger.info("🗑️  Deleting files...")
            cleanup_deleted_files()

    except Exception as e:
        logger.error(f"❌ Critical error occurred: {e}")


if __name__ == "__main__":
    main()
