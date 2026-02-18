from PIL import Image
import numpy as np
import tensorflow as tf

# Model input configuration
IMAGE_SIZE = (224, 224)


def preprocess_image(image_path: str) -> tf.Tensor:
    """
    Load an image from disk and preprocess it for the embedding model.

    Steps:
    - Load image
    - Convert to RGB
    - Resize to model input size
    - Normalize pixel values to [0, 1]
    - Add batch dimension

    Returns:
        Tensor of shape (1, 224, 224, 3), dtype float32
    """

    # 1. Load image
    image = Image.open(image_path).convert("RGB")

    # 2. Resize
    image = image.resize(IMAGE_SIZE)

    # 3. Convert to numpy array
    image_array = np.array(image).astype("float32")

    # 4. Normalize to [0, 1]
    image_array /= 255.0

    # 5. Add batch dimension
    image_array = np.expand_dims(image_array, axis=0)

    # 6. Convert to TensorFlow tensor
    image_tensor = tf.convert_to_tensor(image_array, dtype=tf.float32)

    return image_tensor
