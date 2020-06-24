# -*- coding: utf-8 -*-
"""soultion.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NcQIX962QiMypfxI0GLyrilNcbPlc7bE
"""

import pymongo
import pandas as pd
import numpy as np
import matplotlib
from pandas.plotting import scatter_matrix
from matplotlib import pyplot as plt
import random
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from keras.utils import to_categorical
from keras.models import Model, Input, Sequential
from keras.layers import LSTM, Dense, Dropout, RepeatVector, TimeDistributed

"""## Dataset
There are two different kinds of data available.

It is entirely up to you which set of data you work with, you may experiment with both
and choose one that produces the best results or you can use both if you wish.

Each dataset has 2 types of information, prices and sentiment.
"""

mongo_client = pymongo.MongoClient(
'mongodb://mlcandidates:crackthecode@100.2.158.147:27017/')
finDb = mongo_client['findata']

intradayCollection = finDb['intraday']
dailyCollection = finDb['day']

"""1. Minute data where each row in the dataframe represents one minute (intradayCollection)"""

# To get all of the symbols available in the collection
all_unique_intraday_symbols = intradayCollection.distinct('Symbol')

# To get data for a specific symbol
msft_intraday_df = pd.DataFrame(list(intradayCollection.find({'Symbol': 'MSFT', 'close': {'$exists':True}})))

# To get data for all symbols
# all_stocks_intraday_df = pd.DataFrame(list(intradayCollection.find({'close':{'$exists':True}})))

"""Selecting random symbols from the list. This block of code can be used to select one or multiple symbols at random from the list by changing the sample size (currently set at 50). Current analysis has only been done for 'MSFT' symbol."""

print(len(all_unique_intraday_symbols))
intraday_symbols_sample = random.sample(all_unique_intraday_symbols, 50)
print(intraday_symbols_sample)

"""## Observing the Dataset

### Trivial and Statistical Analysis of the dataset
"""

print(msft_intraday_df.shape)
print(msft_intraday_df.head(10))
print(msft_intraday_df.columns.values)

print(msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']].describe())

"""### Data Visualization"""

# box and whisker plots
msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']].plot(kind='box', subplots=True, layout=(1,5), sharex=False, sharey=False)
plt.show()
msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']].hist()
plt.show()
scatter_matrix(msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']])
plt.show()

"""## Evaluating Some Machine Learning Algorithms"""

#setting index as date
df = msft_intraday_df
df['Date'] = pd.to_datetime(df.Date,format='%Y-%m-%d')
df.index = df['Date']

plt.figure(figsize=(20,10))
plt.plot(df['close'], label='Close Price history')

"""### Moving Average"""

#creating dataframe with date and the target variable
data = df.sort_index(ascending=True, axis=0)
new_data = pd.DataFrame(index=range(0,len(df)),columns=['Date', 'close'])

for i in range(0,len(data)):
     new_data['Date'][i] = data['Date'][i]
     new_data['close'][i] = data['close'][i]

# splitting into train and validation
train = new_data[:7500]
valid = new_data[7500:]

# In the next step, we will create predictions for the validation set and check the RMSE using the actual values.
# making predictions using Moving average
preds = []
for i in range(0,valid.shape[0]):
    a = train['close'][len(train)-2048+i:].sum() + sum(preds)
    b = a/2048
    preds.append(b)

# checking the results
mse=np.mean(np.power((np.array(valid['close'])-preds),2))
rms=np.sqrt(np.mean(np.power((np.array(valid['close'])-preds),2)))
print(f"MSE: {mse} RMS: {rms}")

valid.insert(2, 'Predictions', preds, True)
plt.figure(figsize=(20,10))
plt.plot(train['close'])
plt.plot(valid[['close', 'Predictions']])

"""### Linear Regression"""

# splitting into train and validation
train = msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']][:7500]
valid = msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']][7500:]

x_train = train.drop('close', axis=1)
y_train = train['close']
x_valid = valid.drop('close', axis=1)
y_valid = valid['close']

#implement linear regression
from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(x_train,y_train)

preds = model.predict(x_valid)

# checking the results
mse=np.mean(np.power((np.array(valid['close'])-preds),2))
rms=np.sqrt(np.mean(np.power((np.array(valid['close'])-preds),2)))
print(f"MSE: {mse} RMS: {rms}")

valid.insert(2, 'Predictions', preds, True)
plt.figure(figsize=(20,10))
plt.plot(train['close'])
plt.plot(valid[['close', 'Predictions']])

"""### LSTM for Sequence prediction"""

#creating dataframe
data = df.sort_index(ascending=True, axis=0)
data = data[['Date', 'close']]
new_data = data.copy(deep = True)

#setting index
new_data.index = new_data.Date
new_data.drop('Date', axis=1, inplace=True)

#creating train and test sets
dataset = new_data.values

train = dataset[0:7500,:]
valid = dataset[7500:,:]

#converting dataset into x_train and y_train
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)

x_train, y_train = [], []
for i in range(60,len(train)):
    x_train.append(scaled_data[i-60:i,0])
    y_train.append(scaled_data[i,0])
x_train, y_train = np.array(x_train), np.array(y_train)

x_train = np.reshape(x_train, (x_train.shape[0],x_train.shape[1],1))

# create and fit the LSTM network
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1],1)))
model.add(LSTM(units=50))
model.add(Dense(1))

model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(x_train, y_train, epochs=3, batch_size=1)

"""#### Validation
The number of prior datapoints used as input defines the one-dimensional (1D) subsequence of data that the LSTM will read and learn to extract features. We denote it here by `subsequence_length` which takes the past hour of data. We can also tune this hyperparameter using cross validation across multiple validatin datasets to arrive at an optimal value
"""

subsequence_length = 60 #past one hour
#predicting next values, using past 60 from the train data
inputs = new_data[len(new_data) - len(valid) - subsequence_length:].values
inputs = inputs.reshape(-1,1)
inputs  = scaler.transform(inputs)

X_test = []
for i in range(60,inputs.shape[0]):
    X_test.append(inputs[i-60:i,0])
X_test = np.array(X_test)

X_test = np.reshape(X_test, (X_test.shape[0],X_test.shape[1],1))
closing_price = model.predict(X_test)
closing_price = scaler.inverse_transform(closing_price)
# rms1 = np.sqrt(np.mean(np.power((valid-closing_price),2)))
# print(rms1)
mse=np.mean(np.power((np.array(valid) - closing_price),2))
rms=np.sqrt(np.mean(np.power((np.array(valid) - closing_price),2)))
print(f"MSE: {mse} RMS: {rms}")

"""#### Plot"""

#for plotting
training = new_data[:7500]
validation = new_data[7500:]
validation.insert(2, 'Predictions', closing_price, True)
plt.figure(figsize = (20, 10))
plt.plot(training['close'])
plt.plot(validation[['close','Predictions']])

"""### Multivariate LSTM for Sequence Prediction"""

#creating dataframe
data = df.sort_index(ascending=True, axis=0)
data = data[['Date', 'close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']]
new_data = data.copy(deep = True)

#setting index
new_data.index = new_data.Date
new_data.drop('Date', axis=1, inplace=True)

#creating train and test sets
dataset = new_data.values

# train = msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']][0:7500,:]
# valid = msft_intraday_df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']][7500:,:]
train = dataset[0:7500,:]
valid = dataset[7500:,:]

#converting dataset into x_train and y_train
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)

x_train, y_train = [], []
for i in range(60,len(train)):
    x_train.append(scaled_data[i-60:i,0])
    y_train.append(scaled_data[i,0])
x_train, y_train = np.array(x_train), np.array(y_train)

x_train = np.reshape(x_train, (x_train.shape[0],x_train.shape[1],1))

# create and fit the LSTM network
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1],1)))
model.add(LSTM(units=50))
model.add(Dense(1))

model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(x_train, y_train, epochs=3, batch_size=1)

"""#### Validation
The number of prior datapoints used as input defines the one-dimensional (1D) subsequence of data that the LSTM will read and learn to extract features. We denote it here by `subsequence_length` which takes the past hour of data. We can also tune this hyperparameter using cross validation across multiple validatin datasets to arrive at an optimal value
"""

subsequence_length = 60 #past one hour
#predicting next values, using past 60 from the train data
inputs = new_data[len(new_data) - len(valid) - subsequence_length:].values
inputs = inputs.reshape(-1,5)
inputs  = scaler.transform(inputs)
X_test = []
for i in range(60,inputs.shape[0]):
    X_test.append(inputs[i-60:i,0])
X_test = np.array(X_test)

X_test = np.reshape(X_test, (X_test.shape[0],X_test.shape[1],1))
closing_price = model.predict(X_test)
closing_price = np.concatenate((closing_price, np.zeros((closing_price.shape[0],4))), axis = 1)
closing_price = scaler.inverse_transform(closing_price)

closing_price = closing_price[:,:1]
# print(closing_price)
# print(valid[:,:1])
mse=np.mean(np.power((np.array(valid[:,:1]) - closing_price),2))
rms=np.sqrt(np.mean(np.power((np.array(valid[:,:1]) - closing_price),2)))
print(f"MSE: {mse} RMS: {rms}")

"""#### Plot"""

training = new_data[['close']][:7500]
validation = new_data[['close']][7500:]
validation.insert(2, 'Predictions', closing_price, True)
plt.figure(figsize = (20, 10))
plt.plot(training['close'])
plt.plot(validation[['close','Predictions']])

"""### Multivariate LSTM with seq2seq (Encoder-Decoder LSTM) (*Not Working, Disregard*)"""

dataset = df[['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']].copy(deep = True)
dataset = dataset[:(df.shape[0]-(df.shape[0]%10))]
# dataset.drop('Date', inplace=True, axis=1)
print(dataset.shape)

# split into standard weeks
train, test = dataset.values[0:7500], dataset.values[7500:]

# restructure into windows of weekly data
# print(train.shape) # (750, 10, 5)
train = np.array(np.split(train, len(train)/10))
# print(test.shape)
test = np.array(np.split(test, len(test)/10))

n_input = 10

# prepare data
n_out=1
# flatten data
data = train.reshape((train.shape[0]*train.shape[1], train.shape[2]))
print(data)
print(data.shape)
print(train.shape)
X, y = list(), list()
in_start = 0
# step over the entire history one time step at a time
for _ in range(len(data)):
  # define the end of the input sequence
  in_end = in_start + n_input
  out_end = in_end + n_out
  # ensure we have enough data for this instance
  if out_end < len(data):
    # print(len(data))
    X.append(data[in_start:in_end, :])
    y.append(data[in_end:out_end, 0])
  # move along one time step
  in_start += 1
# print(np.array(X).shape)
train_x, train_y = np.array(X), np.array(y)
(750, 10, 5)
# define parameters
epochs, batch_size = 50, 60
n_timesteps, n_features, n_outputs = train_x.shape[1], train_x.shape[2], train_y.shape[1]
# reshape output into [samples, timesteps, features]
train_y = train_y.reshape((train_y.shape[0], train_y.shape[1], 1))
# define model
model = Sequential()
model.add(LSTM(200, activation='relu', input_shape=(n_timesteps, n_features)))
model.add(RepeatVector(n_outputs))
model.add(LSTM(200, activation='relu', return_sequences=True))
model.add(TimeDistributed(Dense(100, activation='relu')))
model.add(TimeDistributed(Dense(1)))
model.compile(loss='mse', optimizer='adam')
# fit network
model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size)

history = [x for x in train]
predictions = list()
for i in range(len(test)):
  # flatten data
  data = np.array(history)
  data = data.reshape((data.shape[0]*data.shape[1], data.shape[2]))
  # retrieve last observations for input data
  input_x = data[-n_input:, :]
  input_x = input_x.reshape((1, input_x.shape[0], input_x.shape[1]))
  yhat = model.predict(input_x, verbose=0)
  # we only want the vector forecast
  yhat_sequence = yhat[0]
  # store the predictions
  predictions.append(yhat_sequence)
  # get real observation and add to history for predicting the next minute
  history.append(test[i, :])
predictions = np.array(predictions)
actual = test[:, :, 0]

mse=np.mean(np.power((np.array(actual) - predictions),2))
rms=np.sqrt(np.mean(np.power((np.array(actual) - predictions),2)))
print(f"MSE: {mse} RMS: {rms}")

predictions = predictions.reshape((predictions.shape[0],1))

training = dataset[['close']][:7500 ]
validation = dataset[['close']][-len(predictions):]
validation['Predictions'] = predictions
plt.figure(figsize = (20, 10))
plt.plot(training['close'])
plt.plot(validation[['close','Predictions']])

# Commented out IPython magic to ensure Python compatibility.
# %time test_intraday_df = pd.DataFrame(list(intradayCollection.find({'Symbol': { '$in': intraday_symbols_sample}, 'close': {'$exists':True}})))

test_intraday_df.shape

"""datapoints: ['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']
the goal is to predict the 'close' using any combination of the other data points.


2. Daily data where each row in the dataframe represents one day (dailyCollection)
"""

# To get all of the symbols available in the collection
all_unique_daily_symbols = dailyCollection.distinct('Symbol')

print(len(all_unique_daily_symbols))
daily_symbols_sample = random.sample(all_unique_daily_symbols, 300)
print(daily_symbols_sample)

# Commented out IPython magic to ensure Python compatibility.
# To get data for a specific symbol
# %time msft_daily_df = pd.DataFrame(list(dailyCollection.find({'Symbol': 'MSFT', 'close': {'$ne': 'NaN'}})))

len(all_unique_daily_symbols)
print(msft_daily_df.shape)

print(msft_intraday_df.columns.values)
msft_daily_df[['Close', 'Volume', 'volume_change', 'volume_score', 'bullish', 'bearish']]

all_stocks_daily_df = pd.DataFrame(list(dailyCollection.find({'close':{'$ne':'NaN'}})))

"""datapoints: ['Close', 'Volume', 'volume_change', 'volume_score', 'bullish', 'bearish']
the goal is to predict the 'Close' using any combination of the other data points.

Once you have completed your code , reach out to me!
"""