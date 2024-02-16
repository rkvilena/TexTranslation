import time
import tensorflow as tf
from tensorflow import keras

class CRNN:
    def __init__(self) -> None:
        self.model = keras.models.load_model("SavedModel", compile=False)
        self.imagelist = []
        self.duration = 0.0

    def _read_image(self, image):
        img = tf.convert_to_tensor(image)
        return img
    
    def _resize_to_input_ch(self, image):
        img_shape = tf.shape(image)
        scale_factor = 32 / img_shape[0]
        img_width = scale_factor * tf.cast(img_shape[1], tf.float64)
        img_width = tf.cast(img_width, tf.int32)
        img = tf.image.resize(image, (32, img_width))
        img = tf.expand_dims(img, 0)
        return img

    def exec(self, image_arr):
        start = time.time()
        img = self._read_image(image_arr)
        img = self._resize_to_input_ch(img)
        outputs = self.model(img)
        self.duration += (time.time() - start)
        print(
            f"y_pred: {outputs[0].numpy()}, "
            f"probability: {outputs[1].numpy()}",
        )
        return outputs[0].numpy()