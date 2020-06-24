# There are two different kinds of data available.

# It is entirely up to you which set of data you work with, you may experiment with both
# and choose one that produces the best results or you can use both if you wish.

# Each dataset has 2 types of information, prices and sentiment.

import pymongo
import pandas as pd

mongo_client = pymongo.MongoClient(
'mongodb://mlcandidates:crackthecode@100.2.158.147:27017/')
finDb = mongo_client['findata']

intradayCollection = finDb['intraday']
dailyCollection = finDb['day']


# 1. Minute data where each row in the dataframe represents one minute (intradayCollection)

# To get all of the symbols available in the collection
all_unique_intraday_symbols = intradayCollection.distinct('Symbol')

# To get data for a specific symbol
msft_intraday_df = pd.DataFrame(list(intradayCollection.find({'Symbol': 'MSFT', 'close': {'$exists':True}})))


# To get data for all symbols
all_stocks_intraday_df = pd.DataFrame(list(intradayCollection.find({'close':{'$exists':True}})))



# datapoints: ['close', 'volume', 'trending_score', 'sentiment_change', 'volume_change']
# the goal is to predict the 'close' using any combination of the other data points.


# 2. Daily data where each row in the dataframe represents one day (dailyCollection)

# To get all of the symbols available in the collection
all_unique_daily_symbols = dailyCollection.distinct('Symbol')

# To get data for a specific symbol
msft_daily_df = pd.DataFrame(list(dailyCollection.find({'Symbol': 'MSFT', 'close': {'$ne': 'NaN'}})))

# To get data for all symbols
all_stocks_daily_df = pd.DataFrame(list(dailyCollection.find({'close':{'$ne':'NaN'}})))

# datapoints: ['Close', 'Volume', 'volume_change', 'volume_score', 'bullish', 'bearish']
# the goal is to predict the 'Close' using any combination of the other data points.

# Once you have completed your code , reach out to me!
