# -*- coding: utf-8 -*-

import pandas as pd # Module to handle table operations
import tensorflow as tf # Module for deep learning
import sys # Module to use system commands
import tweepy as tw

print('Initializing variables...')
# Code to get user input from command line. Commented out in this example script
mode = sys.argv[1] # Mode: train or predict
if mode == 'train': # Arguments used if training
    epochs = int(sys.argv[2]) # Number of training epochs
    model_save_path = sys.argv[3] # Path to save model
# Example of train command:
#    python sentiment_analysis.py train 20 ./model.tf
    
if mode == 'predict': # Arguments used only if predicting
    phrase = '#'+sys.argv[2] # Searched hashtag
    date_since = sys.argv[3]  # Date in YYYY-MM-DD format
    num_elem = int(sys.argv[4]) # NUmber of tweets (if 0 then no limit)
    model_path = sys.argv[5] # Path to the model you want to use
# Example of predict command:
#    python sentiment_analysis.py trump 2020-12-15 20 ./model.tf

if mode == 'train':
    from sklearn.model_selection import train_test_split
    
    # Data import
    df = pd.read_csv('./train.csv', index_col=0)
    
    # Finding maximum tweet length to use in padding
    tweet_lengths = []
    for tweet in df['tweet']:
        tweet_lengths.append(len(tweet))
    max_tweet_length = (max(tweet_lengths))
    del tweet_lengths
    
    def df_to_dataset(dataframe, batch_size=32):
    # Function to convert pandas dataframe into tensorflow dataset
        dataframe = dataframe.copy()
        labels = dataframe.pop('label')
        ds = tf.data.Dataset.from_tensor_slices((dataframe['tweet'], labels))
        ds = ds.batch(batch_size)
        ds = ds.prefetch(batch_size)
        return ds
    
    # Splitting data into train and validation subsets
    train, val = train_test_split(df, test_size=0.3, random_state=101)

    train_ds = df_to_dataset(train)
    val_ds = df_to_dataset(val)
    
    # Creating a text vectorization layer
    vectorize_layer = tf.keras.layers.experimental.preprocessing.TextVectorization(max_tokens=10000, output_mode='int',
                                                                                   output_sequence_length=274)
    # Creating a dataset that contains only text to fit the encoding vectorization layer
    train_text = train_ds.map(lambda x, y: x)
    # Fitting the layer
    vectorize_layer.adapt(train_text)
    
    # Text preprocessing
    def vectorize_text(text, label):
        text = tf.expand_dims(text[0], -1)
        return vectorize_layer(text), label

    AUTOTUNE = tf.data.experimental.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # Creating the model
    model = tf.keras.Sequential([
        vectorize_layer,
        tf.keras.layers.Embedding(10000, 20),
        tf.keras.layers.Dense(256),
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(1)])
    
    # Checkpoint to save the model with the best validation accuracy
    checkpoint_val_acc = tf.keras.callbacks.ModelCheckpoint(
        model_save_path, monitor='val_binary_accuracy', verbose=1, save_best_only=True,
        save_weights_only=False,  save_freq='epoch')
    
    # Compiling the model
    model.compile(loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
                  optimizer='adam',
                  metrics=tf.metrics.BinaryAccuracy(threshold=0.0))
    
    # Fitting the model
    history = model.fit(train_ds, validation_data=val_ds, epochs=epochs,
                        callbacks=[checkpoint_val_acc])
    
if mode == 'predict':
    
    print('Reading Twitter access and customer tokens...')
    # Imoprting access keys from './access.csv' file
    keys = pd.read_csv('./access.csv', names=['KeyName','Key'])
    keys
    consumer_key= keys['Key'][0]
    consumer_secret=  keys['Key'][1]
    access_token=  keys['Key'][2]
    access_token_secret=  keys['Key'][3]
    
    # Using access keys to log into Twitter API
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)
    
    if num_elem>0:
        # Retrieve set number of tweets
        tweets = tw.Cursor(api.search,
                      q=phrase,
                      lang="en",
                      since=date_since).items(num_elem)
    else:
        # Retrieve all tweets
        tweets = tw.Cursor(api.search,
                      q=phrase,
                      lang="en",
                      since=date_since).items()
    
    print('Retrieving Tweets, this might take a while...')
    # In the dataset tagged usernames are replaced with "@user" so the same must be done in the new data
    tweets_list = []
    
    for tweet in tweets:
        tweet_text = tweet.text
        text_list = tweet_text.split() # Splitting strings into words to find usernames beginning with @
        for idx, item in enumerate(text_list):
            if '@' in item:
                text_list[idx] = '@user'
    
        text = ' '.join([str(elem) for elem in text_list]) # Merging list back into string
        tweets_list.append(text)
        
    # Creating a function that converts tweet list into TF Dataset
    def sample_list_to_dataset(dataframe, batch_size=20):
        ds = tf.data.Dataset.from_tensor_slices(dataframe)
        ds = ds.batch(batch_size)
        ds = ds.prefetch(batch_size)
        return ds
    
    # Loading in model
    model_2 = tf.keras.models.load_model(model_path)
    
    # Creating the prediction dataset
    predict_ds = sample_list_to_dataset(tweets_list)
    # Predicting
    score = model_2.predict(predict_ds)
    y_pred = []
    for i in score:
        if i >=0.5:
            y_pred.append(1)
        else:
            y_pred.append(0)
            
    negative_count = sum(y_pred)
    negative_percent = (negative_count/len(y_pred))*100
    positive_percent = ((len(y_pred)-negative_count)/len(y_pred))*100
    print('\n FINISHED \n')
    print('Processed %d Tweets; %.2f %% were negative and %.2f %% were positive' % 
          (len(y_pred), negative_percent, positive_percent))