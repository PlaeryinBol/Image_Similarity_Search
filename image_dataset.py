from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

import config

TRANSFORMS = transforms.Compose(
    [
        transforms.Resize((config.EMBEDDING_SIZE, config.EMBEDDING_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
    ]
)


class ImageDataset(Dataset):
    def __init__(self, image_paths):
        """
        Custom dataset for loading and transforming images.

        Args:
            image_paths (list): List of image file paths.
        """
        self.image_paths = image_paths

    def __getitem__(self, index):
        image_path = self.image_paths[index]
        image = Image.open(image_path).convert("RGB")
        if TRANSFORMS is not None:
            image = TRANSFORMS(image)
        return image, image_path

    def __len__(self):
        return len(self.image_paths)
