import tensorflow as tf


class baseInteraction( tf.keras.layers.Layer ):
    def __init__(self):
        super(baseInteraction, self).__init__()
        pass


    def call(self, x):
        pass


class InnerProductInteraction( baseInteraction ):
    '''
    latent factor mapper for cateory datas
    '''
    def __init__(self):
        super( InnerProductInteraction, self ).__init__()

    def call(self, embed1, embed2):
        x = embed1 * embed2
        return x


class MLPInteraction_legency( baseInteraction ):
    '''
    latent factor mapper for cateory datas
    '''
    def __init__(self):
        super( MLPInteraction, self ).__init__()
        self.dense_layers = []
        self.dense_layers.append( tf.keras.layers.Dense(128) )
        self.dense_layers.append( tf.keras.layers.Dense( 128 ) )
        self.dense_layers.append( tf.keras.layers.Dense( 128 ) )
        self.dense_layers.append( tf.keras.layers.Dense( 64 ) )

    def call(self, embeds ):
        x = tf.concat( embeds, axis = 1 )
        for layer in self.dense_layers:
            x = layer( x )
        return x



class MLPInteraction( baseInteraction ):
    '''
    latent factor mapper for cateory datas
    '''
    def __init__(self):
        super( MLPInteraction, self ).__init__(  )
        self.dense_layers = []
        self.dense_layers.append( tf.keras.layers.Dense(128) )
        self.dense_layers.append( tf.keras.layers.Dense( 128 ) )
        self.dense_layers.append( tf.keras.layers.Dense( 128 ) )
        self.dense_layers.append( tf.keras.layers.Dense( 64 ) )

    def call(self, embeds):
        x = tf.concat( embeds , axis = 1 )
        for layer in self.dense_layers:
            x = layer( x )
        return x
