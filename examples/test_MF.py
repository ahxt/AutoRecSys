## code=utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import tensorflow as tf
from autorecsys.recommender import Recommender
from autorecsys.trainer import train

if __name__ == "__main__":

    # set GPU devices
    gpus = tf.config.experimental.list_physical_devices('GPU')
    print("Available GPUs: {}".format(gpus))
    assert len(gpus) > 0, "Not enough GPU hardware devices available"
    # tf.config.experimental.set_memory_growth(gpus[0], True)
    tf.config.experimental.set_visible_devices(gpus[0], 'GPU')

    # load dataset
    used_column = [0, 1, 2]
    record_defaults = [tf.int32, tf.int32, tf.float32]
    data = tf.data.experimental.CsvDataset("./tests/datasets/ml-1m/ratings.dat", record_defaults,
                                           field_delim=",", select_cols=used_column)
    data = data.repeat().shuffle(buffer_size=1000).batch(batch_size=10240).prefetch(buffer_size=5)

    # build recommender
    model = Recommender("config.yaml")

    # train model
    train(model, data)
