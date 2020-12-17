# -*- coding: utf-8 -*-
"""
@author: Łukasz Ozimek 236529
"""
import numpy as np # Module for numercial operations
import pandas as pd # Module to handle table operations
import tensorflow as tf # Module for deep learning
import sys # Module to use system commands
import matplotlib.pyplot as plt # Module to draw graphs and plots
import os

print('Initializing variables')
mode = sys.argv[1] == 'train' # Getting boolean value from command line
save = sys.argv[2] == 'save' # Getting boolean value from command line
if len(sys.argv)>3: # Model name as optional argument
    model_name = './models/' + sys.argv[3] # Getting model path
else:
    model_name = ''
train_data_dir = './training_sets/TRAIN' #Directory of training data
validation_data_dir = './training_sets/VAL' #Directory of validation data
test_data_dir = './predict_imgs' #Directory of test data
img_size = (250, 250) # Image size
batch_size = 20 # Batch size for generator



if mode:
    print('Reading images')
    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            rescale=1./255, # normalizing pixel values from [0,255] to [0,1]
            shear_range=0.2, 
            zoom_range=0.2,  
            rotation_range=20, 
            width_shift_range=0.2, 
            height_shift_range=0.2,
            horizontal_flip=True) 

    val_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
             rescale=1./255)

    # Creating training set with data augumentation
    train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='binary')

    # Creating validation set without data augumentation
    validation_generator = val_datagen.flow_from_directory(
        validation_data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='binary')

    print('Creating model')
    base_model = tf.keras.applications.InceptionV3(weights='imagenet', include_top=False,
                                                   input_shape=(img_size[0], img_size[1], 3))
    model_top = tf.keras.models.Sequential()
    model_top.add(tf.keras.layers.GlobalAveragePooling2D(input_shape=base_model.output_shape[1:], data_format=None)),  
    model_top.add(tf.keras.layers.Dense(256, activation='relu'))
    model_top.add(tf.keras.layers.Dropout(0.5))
    model_top.add(tf.keras.layers.Dense(1, activation='sigmoid')) 

    model = tf.keras.Model(inputs=base_model.input, outputs=model_top(base_model.output))

    model.compile(optimizer=tf.keras.optimizers.Adam(lr=0.0001, beta_1=0.9, beta_2=0.999, epsilon=1e-08,decay=0.0), 
                  loss=tf.keras.losses.BinaryCrossentropy(), metrics=['accuracy'])
    
    print('Commencing training')
    if save: # Training and saving
        # Callback to save model if validation accuracy improves
        checkpoint_val_acc = tf.keras.callbacks.ModelCheckpoint(
                model_name, monitor='val_loss', verbose=1, save_best_only=True,
                save_weights_only=False,  save_freq='epoch' )

        history = model.fit(train_generator,
                    batch_size= batch_size,
                    callbacks=[checkpoint_val_acc],
                    epochs=15,
                    validation_data=validation_generator)
    else: # Only training
        history = model.fit(train_generator,
                    batch_size= batch_size,
                    epochs=15,
                    validation_data=validation_generator)
        
    print('Training complete, model saved' if save else 'Training complete, model not saved')
    
    print('Drawing training plot')
    plt.figure(figsize=(10,10))
    plt.plot(history.history['accuracy'], 'orange', label='Training accuracy')
    plt.plot(history.history['val_accuracy'], 'blue', label='Validation accuracy')
    plt.plot(history.history['loss'], 'red', label='Training loss')
    plt.plot(history.history['val_loss'], 'green', label='Validation loss')
    plt.legend()
    plt.savefig('./metrics/Training_parameters.png')
    print('Plot finished, it is in the metrics folder')
    
if not mode:
    model = tf.keras.models.load_model(model_name) # load model
    
print('Commencing prediction')

y_pred = [] # List of predictions
file_list = os.listdir('./predict_imgs/') # List of all files in the directory
for file in file_list:
    path = './predict_imgs/' + file
    img = tf.keras.preprocessing.image.load_img(path, target_size=img_size) # Importing image
    img = tf.keras.preprocessing.image.img_to_array(img) # Converting image to numpy array
    x = np.expand_dims(img, axis=0) * 1./255 # Normalizing an array and converting it from (height, width, channels) 
#to (batchs size, height, width, channels)
    score = model.predict(x) # Predicit score
    y_pred.append('Chest X-ray' if score<0.5 else 'Abd X-ray')

df = pd.DataFrame() # Creating a dataframe to save to csv
df['File name'] = file_list # Adding file names
df['Class'] = y_pred # Adding predicted classes
df.to_csv('./metrics/report.csv', index = False) # Writing outcome to file
print('Prediction complete, report is in the metrics folder')
print('DONE!')