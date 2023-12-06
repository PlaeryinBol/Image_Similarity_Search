import glob
import json
import logging
import os
import shutil
from collections import defaultdict

import pandas as pd
import torch
from PIL import Image, ImageChops
from scipy.spatial.distance import cdist
from sklearn.cluster import DBSCAN
from tqdm import tqdm

import config
from encoder import EncoderCNN
from image_dataset import ImageDataset

logging.basicConfig(filename="app.log", level=logging.INFO, filemode="w")
log = logging.getLogger()


class ImageProcessor():
    def __init__(self):
        self.image_paths = glob.glob(f"{config.IMAGE_DIR}/**/*.*", recursive=True)
        self.image_paths = [file for file in self.image_paths if file.endswith(config.IMAGE_EXTENSIONS)]
        self.find_identical_images()

        self.dataset = ImageDataset(self.image_paths)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.features_df = self.create_features_df()

    def find_identical_images(self):
        """Finds identical images based on file size and removes duplicates if specified."""
        size_dict = {}
        duplicates_info = defaultdict(lambda: {'duplicates_count': 0, 'duplicates': []})
        duplicates = defaultdict(set)
        for filename in tqdm(self.image_paths, desc='Find identical images'):
            filename = os.fsdecode(filename)
            f_info = os.stat(filename)

            if f_info.st_size not in size_dict:
                size_dict[f_info.st_size] = filename
            else:
                image_1 = Image.open(filename).convert('RGB')
                image_2 = Image.open(size_dict[f_info.st_size]).convert('RGB')
                difference = ImageChops.difference(image_1, image_2)
                diff_bbox = difference.getbbox()

                if diff_bbox is not None:
                    continue

                duplicates[f_info.st_size].add(filename)
                duplicates_info[size_dict[f_info.st_size]]['duplicates_count'] += 1
                duplicates_info[size_dict[f_info.st_size]]['duplicates'].append(filename)

        log.info(f'Found {len(duplicates)} identical images')
        log.info(json.dumps(duplicates_info, indent=4))

        if config.REMOVE_DUPLICATES:
            for f in duplicates_info:
                for d in duplicates_info[f]['duplicates']:
                    os.remove(d)

        self.image_paths = list(set(self.image_paths) - set(duplicates))
        return

    def create_features_df(self):
        """
        Creates a DataFrame of image features using an encoder model.
        If the DataFrame already exists, it is loaded from disk.
        Returns:
            The DataFrame of image features.
        """
        if os.path.exists(config.FEATURES_DF_PATH):
            features_df = pd.read_table(config.FEATURES_DF_PATH)
            return features_df

        dataloader = torch.utils.data.DataLoader(self.dataset, batch_size=config.BATCH_SIZE, shuffle=False)
        encoder = EncoderCNN().to(self.device).eval()

        data = []
        for images_batch, paths in tqdm(dataloader, desc="Create features df"):
            images = images_batch.to(self.device)
            encoder.zero_grad()
            with torch.no_grad():
                features = encoder(images)
            batch_df = pd.DataFrame(features.cpu().numpy(), index=paths)
            data.append(batch_df)

        features_df = pd.concat(data).reset_index(drop=True)
        features_df.insert(0, 'image_paths', self.image_paths)
        features_df.to_csv(config.FEATURES_DF_PATH, sep='\t', index=False)
        return features_df

    def find_similar_by_distance(self):
        """
        Finds similar images based on distance between their features.
        Returns:
            A tuple containing a dictionary of image information and a set of similar images.
        """
        distances = cdist(self.features_df.iloc[:, 1:].values, self.features_df.iloc[:, 1:].values, metric='euclidean')

        similar_images, image_info = set(), {}
        for i in tqdm(range(len(distances)), desc="Search similar by distance"):
            for j in range(i+1, len(distances)):

                if distances[i, j] > config.DISTANCE_THRESHOLD:
                    continue

                first_img = self.features_df['image_paths'][i]
                second_img = self.features_df['image_paths'][j]
                similar_images.add(second_img)

                if first_img in image_info:
                    image_info[first_img].append(second_img)
                else:
                    image_info[first_img] = [second_img]

        return image_info, similar_images

    def find_similar_by_dbscan(self):
        """
        Finds similar images using the DBSCAN clustering algorithm.
        Returns:
            A tuple containing a dictionary of image information and a set of similar images.
        """
        print('Start DBSCAN clustering...')
        model = DBSCAN(min_samples=config.MIN_CLUSTER_SAMPLES, eps=config.DBSCAN_EPSILON, n_jobs=-1)
        predicted_labels = model.fit_predict(self.features_df.iloc[:, 1:].values)
        clusters = (pd.DataFrame({"image_paths": self.features_df['image_paths'], "label": predicted_labels})
                    .sort_values(["label", "image_paths"], ascending=False))

        # select one of elements from each cluster to keep
        list_to_keep = set(clusters.groupby("label")["image_paths"].first())
        all_files = set(clusters["image_paths"])
        similar_images = all_files - list_to_keep

        image_info = {}
        for _, paths in clusters[clusters["label"].duplicated(keep=False)].groupby("label")["image_paths"]:
            image_info[paths.iloc[0]] = paths.iloc[1:].values

        return image_info, similar_images

    def find_similar(self):
        """
        Finds similar images and performs actions based on the configuration settings.
        If config.PUT_SIMILAR_IN_FOLDERS is True, it creates folders for similar images and copies them into folders.
        If config.REMOVE_SIMILAR is True, it removes the similar images from config.IMAGE_DIR.
        Returns:
            None
        """
        if config.PUT_SIMILAR_IN_FOLDERS:
            shutil.rmtree(config.DIR_FOR_SIMILARS, ignore_errors=True)
            os.makedirs(config.DIR_FOR_SIMILARS)

        if not config.USE_DBSCAN_CLUSTERING:
            image_info, similar_images = self.find_similar_by_distance()
        else:
            image_info, similar_images = self.find_similar_by_dbscan()

        for k, sim in tqdm(image_info.items()):
            log.info(f'Too similar for "{os.path.basename(k)}":\n{list(map(os.path.basename, sim))}\n')
            if config.PUT_SIMILAR_IN_FOLDERS and not config.REMOVE_SIMILAR:
                dir_name = os.path.join(config.DIR_FOR_SIMILARS, os.path.splitext(os.path.basename(k))[0])

                if os.path.exists(dir_name):
                    shutil.rmtree(dir_name)

                os.makedirs(dir_name)
                shutil.copy(k, os.path.join(dir_name, os.path.basename(k)))
                for el in sim:
                    shutil.copy(el, os.path.join(dir_name, os.path.basename(el)))

        if config.REMOVE_SIMILAR and not config.PUT_SIMILAR_IN_FOLDERS:
            for f in similar_images:
                os.remove(f)


if __name__ == '__main__':
    image_processor = ImageProcessor()
    image_processor.find_similar()
