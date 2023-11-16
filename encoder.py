import timm
import torch.nn as nn

import config


class CustomViT(nn.Module):
    def __init__(self):
        """Custom Vision Transformer (ViT) model."""
        super(CustomViT, self).__init__()
        self.vit = timm.create_model(config.IMAGE_ENCODER, pretrained=True)
        self.in_features = self.vit.head.in_features
        self.vit.head = nn.Identity()

    def forward(self, x):
        x = self.vit(x)
        return x


class EncoderCNN(nn.Module):
    def __init__(self):
        """EncoderCNN model for image feature extraction."""
        super(EncoderCNN, self).__init__()
        self.vit = CustomViT()
        for param in self.vit.parameters():
            param.requires_grad_(False)
        self.embed = nn.Linear(self.vit.in_features, config.EMBEDDING_SIZE)

    def forward(self, images):
        features = self.vit(images)
        features = features.view(features.size(0), -1)
        features = self.embed(features)
        return features
