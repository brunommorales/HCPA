from PIL import Image
import numpy as np
import tensorflow as tf


class RetinopathyAnalyzer:
    def __init__(self, model_path: str):
        self.model = tf.keras.models.load_model(model_path)

    def predict(self, image: np.ndarray):
        """
        Takes a preprocessed image (already resized, centered, normalized, and batched)
        and returns the prediction.
        """
        predictions = self.model.predict(image)
        return predictions