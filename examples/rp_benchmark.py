# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "6"

import logging
from autorecsys.auto_search import Search
from autorecsys.pipeline import Input, LatentFactorMapper, RatingPredictionOptimizer, HyperInteraction, MLPInteraction, \
    ElementwiseInteraction
from autorecsys.pipeline.preprocessor import MovielensPreprocessor
from autorecsys.recommender import RPRecommender

# logging setting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def build_mf():
    input = Input(shape=[2])
    user_emb = LatentFactorMapper(feat_column_id=0,
                                  id_num=10000,
                                  embedding_dim=128)(input)
    item_emb = LatentFactorMapper(feat_column_id=1,
                                  id_num=10000,
                                  embedding_dim=128)(input)
    output = ElementwiseInteraction(elementwise_type="innerporduct")([user_emb, item_emb])
    output = RatingPredictionOptimizer()(output)
    model = RPRecommender(inputs=input, outputs=output)
    return model


def build_gmf():
    input = Input(shape=[2])
    user_emb = LatentFactorMapper(feat_column_id=0,
                                  id_num=10000,
                                  embedding_dim=10)(input)
    item_emb = LatentFactorMapper(feat_column_id=1,
                                  id_num=10000,
                                  embedding_dim=10)(input)
    output = ElementwiseInteraction(elementwise_type="innerporduct")([user_emb, item_emb])
    output = RatingPredictionOptimizer()(output)
    model = RPRecommender(inputs=input, outputs=output)
    return model


def build_mlp():
    input = Input(shape=[2])
    user_emb_mlp = LatentFactorMapper(feat_column_id=0,
                                      id_num=10000,
                                      embedding_dim=10)(input)
    item_emb_mlp = LatentFactorMapper(feat_column_id=1,
                                      id_num=10000,
                                      embedding_dim=10)(input)
    output = MLPInteraction()([user_emb_mlp, item_emb_mlp])
    output = RatingPredictionOptimizer()(output)
    model = RPRecommender(inputs=input, outputs=output)
    return model


def build_neumf():
    input = Input(shape=[2])
    user_emb_gmf = LatentFactorMapper(feat_column_id=0,
                                      id_num=10000,
                                      embedding_dim=10)(input)
    item_emb_gmf = LatentFactorMapper(feat_column_id=1,
                                      id_num=10000,
                                      embedding_dim=10)(input)
    innerproduct_output = ElementwiseInteraction(elementwise_type="innerporduct")([user_emb_gmf, item_emb_gmf])

    user_emb_mlp = LatentFactorMapper(feat_column_id=0,
                                      id_num=10000,
                                      embedding_dim=10)(input)
    item_emb_mlp = LatentFactorMapper(feat_column_id=1,
                                      id_num=10000,
                                      embedding_dim=10)(input)
    mlp_output = MLPInteraction()([user_emb_mlp, item_emb_mlp])

    output = RatingPredictionOptimizer()([innerproduct_output, mlp_output])
    model = RPRecommender(inputs=input, outputs=output)
    return model


def build_autorec():
    input = Input(shape=[2])
    user_emb = LatentFactorMapper(feat_column_id=0,
                                  id_num=10000,
                                  embedding_dim=10)(input)
    item_emb = LatentFactorMapper(feat_column_id=1,
                                  id_num=10000,
                                  embedding_dim=10)(input)
    output = HyperInteraction()([user_emb, item_emb])
    output = RatingPredictionOptimizer()(output)
    model = RPRecommender(inputs=input, outputs=output)
    return model


if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-model', type=str, help='input a model name')
    parser.add_argument('-data', type=str, help='dataset name')
    parser.add_argument('-data_path', type=str, help='dataset path')
    parser.add_argument('-search', type=str, help='input a search method name')
    parser.add_argument('-batch_size', type=int, help='batch size')
    parser.add_argument('-trials', type=int, help='try number')
    args = parser.parse_args()
    print("args:", args)

    # Load dataset
    if args.data == "ml":
        data = MovielensPreprocessor(args.data_path)
    if args.data == "netflix":
        data = MovielensPreprocessor(args.data_path)
    data.preprocessing(test_size=0.1, random_state=1314)
    train_X, train_y, val_X, val_y = data.train_X, data.train_y, data.val_X, data.val_y

    # select model
    if args.model == 'mf':
        model = build_mf()
    if args.model == 'mlp':
        model = build_mlp()
    if args.model == 'gmf':
        model = build_gmf()
    if args.model == 'neumf':
        model = build_neumf()
    if args.model == 'autorec':
        model = build_autorec()

    # search and predict.
    cf_searcher = Search(model=model,
                         tuner=args.search,  ## hyperband, bayesian
                         tuner_params={'max_trials': args.trials, 'overwrite': False}
                         )
    cf_searcher.search(x=train_X,
                       y=train_y,
                       x_val=val_X,
                       y_val=val_y,
                       objective='val_mse',
                       batch_size=args.batch_size)
    logger.info('Predicted Ratings: {}'.format(cf_searcher.predict(x=val_X)))
    logger.info('Predicting Accuracy (mse): {}'.format(cf_searcher.evaluate(x=val_X, y_true=val_y)))
