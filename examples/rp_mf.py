# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os

os.environ["CUDA_VISIBLE_DEVICES"] = "5"

import tensorflow as tf
# gpus = tf.config.experimental.list_physical_devices(device_type='GPU')
# for gpu in gpus:
#     tf.config.experimental.set_memory_growth(gpu, True)
# import tensorflow as tf
# physical_devices = tf.config.list_physical_devices('GPU')
# tf.config.experimental.set_memory_growth(physical_devices[0], True)

import logging
from autorecsys.auto_search import Search
from autorecsys.pipeline import Input, LatentFactorMapper, RatingPredictionOptimizer, ElementwiseInteraction
from autorecsys.pipeline.preprocessor import MovielensPreprocessor, NetflixPrizePreprocessor
from autorecsys.recommender import RPRecommender

# logging setting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# load dataset
# dataset_paths = ["./examples/datasets/netflix-prize-data/combined_data_" + str(i) + ".txt" for i in range(1, 5)]
# data = NetflixPrizePreprocessor(dataset_paths)

# data = MovielensPreprocessor("./examples/datasets/ml-1m/ratings.dat")
# data = MovielensPreprocessor("./examples/datasets/ml-10M100K/ratings.dat")
data = MovielensPreprocessor("./examples/datasets/ml-latest/ratings.csv", sep=',')
data.preprocessing(val_test_size=0.1, random_state=1314)
train_X, train_y = data.train_X, data.train_y
val_X, val_y = data.val_X, data.val_y
test_X, test_y = data.test_X, data.test_y
user_num, item_num = data.user_num, data.item_num


print("train_X size:", train_X.shape)
print("train_y size:", train_y.shape)
print("val_X size:", val_X.shape)
print("val_y size:", val_y.shape)
print("test_X size:", test_X.shape)
print("test_y size:", test_y.shape)
print("user number:", user_num)
print("item number:", item_num)

# build the pipeline.
input = Input(shape=[2])
user_emb = LatentFactorMapper(feat_column_id=0,
                              id_num=user_num,
                              embedding_dim=64)(input)
item_emb = LatentFactorMapper(feat_column_id=1,
                              id_num=item_num,
                              embedding_dim=64)(input)
output = ElementwiseInteraction(elementwise_type="innerporduct")([user_emb, item_emb])
output = RatingPredictionOptimizer()(output)
model = RPRecommender(inputs=input, outputs=output)

# AutoML search and predict
searcher = Search(model=model,
                  tuner='greedy',  # hyperband, greedy, bayesian
                  tuner_params={"max_trials": 5}
                  )

searcher.search(x=train_X,
                y=train_y,
                x_val=val_X,
                y_val=val_y,
                objective='val_mse',
                batch_size=256,
                epochs=10,
                callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=1)])

logger.info('Predicted Ratings: {}'.format(searcher.predict(x=val_X)))
logger.info('Predicting Accuracy (mse): {}'.format(searcher.evaluate(x=test_X, y_true=test_y)))
