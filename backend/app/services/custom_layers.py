from tensorflow.keras.layers import Layer # type: ignore
import tensorflow as tf

@tf.keras.utils.register_keras_serializable(package="PetGuard")
class L2Normalize(Layer):
    def __init__(self, axis=1, **kwargs):
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        return tf.nn.l2_normalize(inputs, axis=self.axis)

    def get_config(self):
        config = super().get_config()
        config.update({"axis": self.axis})
        return config
