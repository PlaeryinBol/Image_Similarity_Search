"""
Module for comparing and grouping similar images
"""

import imagehash
from typing import List, Tuple
from pathlib import Path


def are_similar(hash1: imagehash.ImageHash,
                hash2: imagehash.ImageHash, threshold: int) -> bool:
    """
    Determines whether two images are similar based on their hashes

    Args:
        hash1: Hash of the first image
        hash2: Hash of the second image
        threshold: Similarity threshold (the lower, the more similar images must be)

    Returns:
        True if images are similar, False otherwise
    """
    # Calculate Hamming distance between hashes
    distance = hash1 - hash2

    # Compare with threshold
    return distance <= threshold


def find_similar_pairs(
        image_data: List[Tuple[Path, imagehash.ImageHash]], threshold: int) -> List[Tuple[Path, Path]]:
    """
    Finds all pairs of similar images in the list

    Args:
        image_data: List of tuples (file_path, image_hash)
        threshold: Similarity threshold

    Returns:
        List of pairs (path1, path2) of similar images
    """
    similar_pairs = []

    # Compare each image with every other (O(n²))
    for i in range(len(image_data)):
        for j in range(i + 1, len(image_data)):
            path1, hash1 = image_data[i]
            path2, hash2 = image_data[j]

            if are_similar(hash1, hash2, threshold):
                similar_pairs.append((path1, path2))

    return similar_pairs


def group_similar_images(
        similar_pairs: List[Tuple[Path, Path]]) -> List[List[Path]]:
    """
    Groups similar images into connected components

    Args:
        similar_pairs: List of pairs of similar images

    Returns:
        List of groups, where each group is a list of paths to connected images
    """
    if not similar_pairs:
        return []

    # Create sets for each image
    groups = []
    path_to_group = {}  # Dictionary for quick group lookup by path

    for path1, path2 in similar_pairs:
        group1 = path_to_group.get(path1)
        group2 = path_to_group.get(path2)

        if group1 is None and group2 is None:
            # Create a new group
            new_group = [path1, path2]
            groups.append(new_group)
            path_to_group[path1] = new_group
            path_to_group[path2] = new_group

        elif group1 is None:
            # Add path1 to group of path2
            group2.append(path1)
            path_to_group[path1] = group2

        elif group2 is None:
            # Add path2 to group of path1
            group1.append(path2)
            path_to_group[path2] = group1

        elif group1 != group2:
            # Merge two different groups
            # Add all elements of group2 to group1
            group1.extend(group2)
            # Update references for all elements of group2
            for path in group2:
                path_to_group[path] = group1
            # Remove group2 from the list of groups
            groups.remove(group2)

    # Remove duplicates in groups and filter out groups with only one element
    result_groups = []
    for group in groups:
        unique_group = list(set(group))  # Remove duplicates
        if len(unique_group) > 1:  # Keep only groups with multiple elements
            result_groups.append(unique_group)

    # Split large groups into smaller clusters
    final_groups = []
    for group in result_groups:
        if len(group) > 20:  # If the group is too large
            subgroups = split_large_group(group, similar_pairs)
            final_groups.extend(subgroups)
        else:
            final_groups.append(group)

    return final_groups


def split_large_group(
        large_group: List[Path], similar_pairs: List[Tuple[Path, Path]]) -> List[List[Path]]:
    """
    Splits a large group into smaller dense clusters

    Args:
        large_group: Large group of images
        similar_pairs: All pairs of similar images

    Returns:
        List of smaller groups
    """
    # Create a connection graph only within this group
    group_set = set(large_group)
    internal_pairs = [(p1, p2) for p1, p2 in similar_pairs
                      if p1 in group_set and p2 in group_set]

    # Count the number of connections for each image
    connection_count = {}
    for path in large_group:
        connection_count[path] = 0

    for p1, p2 in internal_pairs:
        connection_count[p1] += 1
        connection_count[p2] += 1

    # Sort by number of connections (most connected first)
    sorted_paths = sorted(
        large_group,
        key=lambda x: connection_count[x],
        reverse=True)

    # Create clusters starting from the most connected images
    clusters = []
    used_paths = set()

    for seed_path in sorted_paths:
        if seed_path in used_paths:
            continue

        # Create a new cluster around this image
        cluster = [seed_path]
        used_paths.add(seed_path)

        # Find all directly connected images
        connected = set()
        for p1, p2 in internal_pairs:
            if p1 == seed_path and p2 not in used_paths:
                connected.add(p2)
            elif p2 == seed_path and p1 not in used_paths:
                connected.add(p1)

        # Add connected images to the cluster
        for path in connected:
            if path not in used_paths:
                cluster.append(path)
                used_paths.add(path)

        # Add the cluster only if it has more than one image
        if len(cluster) > 1:
            clusters.append(cluster)

    # If there are unused images left, create separate mini-clusters from them
    remaining = [path for path in large_group if path not in used_paths]
    if len(remaining) > 1:
        clusters.append(remaining)

    return clusters if clusters else [large_group]
