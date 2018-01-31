import matplotlib.pyplot as plt
from stock_object import Stock
import numpy
import math
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
import os
from rnn.data_preprocessor import DataPreprocessor
import pendulum


os.chdir("..\\")
def predict(stock_name, date, timeshift=1):
    end_date = pendulum.parse(date).subtract(days=1)
    start = pendulum.parse(date).subtract(days=1)
    stock_obj = Stock("2888.HK", start_date="2017-01-01", end_date="2017-11-30")
    stock_obj.fill_sparse()
    full_data = stock_obj.get_daily_adj_close_price()
    full_data_count = len(full_data)
    full_data = numpy.array(full_data).reshape(-1, 1)
    scalar = MinMaxScaler(feature_range=(0, 1))
    full_data = scalar.fit_transform(full_data)

    train_size = math.ceil(len(full_data) / 2)
    train_data = full_data[0:train_size]
    test_data = full_data[train_size:]

    time_shift = 15
    train_processor = DataPreprocessor(train_data)
    train_processor.add_feature(train_data)
    train_feature, train_target = train_processor.build(time_shift=time_shift)
    test_preprocessor = DataPreprocessor(test_data)
    test_preprocessor.add_feature(test_data)
    test_feature, test_target = test_preprocessor.build(time_shift=time_shift)

    model = Sequential()
    model.add(Dense(100, input_shape=(train_feature.shape[1], train_feature.shape[2])))
    model.add(LSTM(100))
    #model.add(LSTM(100, input_shape=(time_shift, 1)))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(train_feature, train_target, epochs=100, batch_size=time_shift, verbose=2)

    train_prediction = model.predict(train_feature)
    test_prediction = model.predict(test_feature)

    train_prediction = scalar.inverse_transform(train_prediction).flatten()
    test_prediction = scalar.inverse_transform(test_prediction).flatten()
    full_data = scalar.inverse_transform(full_data)

    train_prediction = numpy.pad(train_prediction, (time_shift, 0), "constant", constant_values=numpy.nan)
    test_prediction = numpy.pad(test_prediction, (len(train_prediction) + time_shift, 0), "constant", constant_values=numpy.nan)

    # train_prediction = numpy.pad(train_prediction, (0, time_shift), "constant", constant_values=numpy.nan)
    # test_prediction = numpy.pad(test_prediction, (len(train_prediction), 0), "constant", constant_values=numpy.nan)

    plt.plot(full_data, label='Original')
    plt.plot(train_prediction, label='Train')
    plt.plot(test_prediction, label='Test')
    plt.legend()
    plt.show()