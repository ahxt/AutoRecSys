from __future__ import absolute_import, division, print_function, unicode_literals

import tensorflow as tf
from tensorflow.python.util import nest

from autorecsys.pipeline.base import Block



class ConcatenateInteraction(Block):
    """
    latent factor interactor for category datas
    """
    def build(self, hp, inputs=None):
        if not isinstance(inputs, list) or len(inputs) != 2:
            raise ValueError("Inputs of ConcatenateInteraction should be a list of length 2.")

        output_node = tf.concat(inputs, axis=0)
        return output_node


class ElementwiseAddInteraction(Block):
    """
    latent factor interactor for category datas
    """
    def build(self, hp, inputs=None):
        if not isinstance(inputs, list) or len(inputs) != 2:
            raise ValueError("Inputs of ElementwiseAddInteraction should be a list of length 2.")

        output_node = tf.add(inputs[0], inputs[1])
        return output_node


class InnerProductInteraction(Block):
    """
    latent factor interactor for category datas
    """
    def build(self, hp, inputs=None):
        if not isinstance(inputs, list) or len(inputs) != 2:
            raise ValueError("Inputs of InnerProductInteraction should be a list of length 2.")

        input_node = inputs
        output_node = input_node[0] * input_node[1]
        return output_node



class MLPInteraction(Block):
    """
    latent factor interactor for cateory data
    """
    def __init__(self,
                 units=None,
                 num_layers=None,
                 use_batchnorm=None,
                 dropout_rate=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.fixed_params = []
        self.tunable_candidates = ['units', 'num_layers', 'use_batchnorm', 'dropout_rate']
        self.units = units
        self.num_layers = num_layers
        self.use_batchnorm = use_batchnorm
        self.dropout_rate = dropout_rate
        self._check_fixed()
        self._hyperparameters = self._get_hyperparameters()

    def get_state(self):
        state = super().get_state()
        state.update({
            'units': self.units,
            'num_layers': self.num_layers,
            'use_batchnorm': self.use_batchnorm,
            'dropout_rate': self.dropout_rate})
        return state

    def set_state(self, state):
        super().set_state(state)
        self.units = state['units']
        self.num_layers = state['num_layers']
        self.use_batchnorm = state['use_batchnorm']
        self.dropout_rate = state['dropout_rate']


    def build(self, hp, inputs=None):

        input_node = tf.concat(inputs, axis=1)
        output_node = input_node
        print( "hp", self.num_layers )

        num_layers = self.num_layers or hp.Choice('num_layers', [1, 2, 3], default=2)
        use_batchnorm = self.use_batchnorm
        if use_batchnorm is None:
            use_batchnorm = hp.Choice('use_batchnorm', [True, False], default=False)
        dropout_rate = self.dropout_rate or hp.Choice('dropout_rate',
                                                      [0.0, 0.25, 0.5],
                                                      default=0)

        for i in range(num_layers):
            units = self.units or hp.Choice(
                'units_{i}'.format(i=i),
                [16, 32, 64, 128, 256, 512, 1024],
                default=32)


        output_node = tf.keras.layers.Dense(units)(output_node)
        if use_batchnorm:
            output_node = tf.keras.layers.BatchNormalization()(output_node)
        output_node = tf.keras.layers.ReLU()(output_node)
        output_node = tf.keras.layers.Dropout(dropout_rate)(output_node)
        return output_node




class HyperInteraction(Block):
    """Combination of serveral interactor into one.
    # Arguments
    meta_interator_num: int
    interactor_type: interactor_name

    """
    def __init__(self, meta_interator_num=None, interactor_type = None, **kwargs):
        super().__init__(**kwargs)
        self.meta_interator_num = meta_interator_num
        self.interactor_type = interactor_type

    # def get_config(self):
    #     config = super().get_config()
    #     config.update({'interactor_type': self.interactor_type})
    #     return config

    # def get_state(self):
    #     state = super().get_state()
    #     state.update({
    #         'interactor_type': self.interactor_type,
    #         'meta_interator_num': self.meta_interator_num
    #     })
    #     return state
    #
    # def set_state(self, state):
    #     super().set_state(state)
    #     self.interactor_type = state['interactor_type']
    #     self.meta_interator_num = state['meta_interator_num']


    def build(self, hp, inputs=None):
        # inputs = nest.flatten(inputs)
        print( "inputs",inputs )

        interactors_name = []
        for i in range(self.meta_interator_num):
            tmp_interactor_type = self.interactor_type or hp.Choice('interactor_type',
                                                  ['InnerProductInteraction', 'ConcatenateInteraction', 'ElementwiseAddInteraction', "MLPInteraction"],
                                                  default='MLPInteraction')
        interactors_name.append( tmp_interactor_type )

        outputs = []
        for interactor_name in interactors_name:
            if interactor_name == "MLPInteraction":
                outputs.append( MLPInteraction(num_layers = 1)(inputs) )
            if interactor_name == "ConcatenateInteraction":
                outputs.append( ConcatenateInteraction.build(hp, inputs) )
            if interactor_name == "ElementwiseAddInteraction":
                outputs.append( ElementwiseAddInteraction.build(hp, inputs) )
            if interactor_name == "InnerProductInteraction":
                outputs.append( ElementwiseAddInteraction.build(hp, inputs) )

        return tf.keras.layers.Concatenate()(outputs)