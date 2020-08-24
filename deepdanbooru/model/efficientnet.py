import numpy as np
import tensorflow as tf
import deepdanbooru as dd


def create_efficientnet_factory(model_name):
    """
    This is a factory that generates functions
    """

    model_generated = getattr(tf.keras.applications, model_name)

    def create_efficientnet(x, output_dim, model=model_generated):
        """
        Efficientnet
        """

        # Load without head
        model = model(include_top=False)

        x = model(x)
        x = dd.model.layers.conv_gap(x, output_dim)
        x = tf.keras.layers.Activation('sigmoid')(x)

        return x

    return create_efficientnet
