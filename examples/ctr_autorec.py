# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "7"

import logging
import tensorflow as tf
import numpy as np
from autorecsys.auto_search import Search
from autorecsys.pipeline import Input, DenseFeatureMapper, SparseFeatureMapper, HyperInteraction, PointWiseOptimizer
from autorecsys.recommender import CTRRecommender
from autorecsys.pipeline.preprocessor import CriteoPreprocessor


# logging setting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Step 1: Preprocess data
criteo = CriteoPreprocessor()  # automatically set up for preprocessing the Criteo dataset
train_X, train_y, val_X, val_y, test_X, test_y = criteo.preprocess()

# Step 2: Build model
dense_input_node = Input(shape=[criteo.get_numerical_count()])
sparse_input_node = Input(shape=[criteo.get_categorical_count()])

dense_feat_emb = DenseFeatureMapper(
    num_of_fields=criteo.get_numerical_count(),
    embedding_dim=2)(dense_input_node)
sparse_feat_emb = SparseFeatureMapper(
    num_of_fields=criteo.get_categorical_count(),
    hash_size=criteo.get_hash_size(),
    embedding_dim=2)(sparse_input_node)

sparse_feat_bottom_output = HyperInteraction(meta_interator_num=2)([sparse_feat_emb])
dense_feat_bottom_output = HyperInteraction(meta_interator_num=2)([dense_feat_emb])
hyper_output = HyperInteraction(meta_interator_num=2)([sparse_feat_bottom_output, dense_feat_bottom_output])

output = PointWiseOptimizer()(hyper_output)
model = CTRRecommender(inputs=[dense_input_node, sparse_input_node], outputs=output)

# Step 3: Build Searcher
searcher = Search(model=model,
                  tuner='random',
                  tuner_params={'max_trials': 2, 'overwrite': True},
                  )

# Step 4: Search model & HP
searcher.search(x=[criteo.get_x_numerical(train_X), criteo.get_x_categorical(train_X)],
                y=train_y,
                x_val=[criteo.get_x_numerical(val_X), criteo.get_x_categorical(val_X)],
                y_val=val_y,
                objective='val_BinaryCrossentropy',
                batch_size=10000,
                epochs = 20,
                callbacks = [ tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=1)] 
                )
logger.info('First 10 Predicted Ratings: {}'.format(searcher.predict(x=[criteo.get_x_numerical(val_X), criteo.get_x_categorical(val_X)])[:10]))
logger.info('Predicting Accuracy (logloss): {}'.format(searcher.evaluate(x=[criteo.get_x_numerical(val_X), criteo.get_x_categorical(val_X)], y_true=val_y)))
