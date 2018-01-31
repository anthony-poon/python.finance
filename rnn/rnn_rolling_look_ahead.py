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

# nb_sample = nb_data_pt - time_shift - look_forward + 1
os.chdir("..\\")
stock_obj = Stock("0700.HK", start_date="2017-01-01", end_date="2017-11-30")
stock_obj.fill_sparse()
unscaled = stock_obj.get_daily_adj_close_price()
full_data_count = len(unscaled)
full_data = numpy.array(unscaled).reshape(-1, 1)
scalar = MinMaxScaler(feature_range=(0, 1))
full_data = scalar.fit_transform(full_data)

train_size = math.ceil(len(full_data) / 2)
train_data = full_data[0:train_size]
test_data = full_data[train_size:]

graph_time_shift = True
time_shift = 15
batch_size = 5
all_result = None
for look_forward in range(1, 30):
    print("------------------------- {0}".format(look_forward))
    train_processor = DataPreprocessor(train_data)
    train_processor.add_feature(train_data)
    train_feature, train_target = train_processor.build(time_shift=time_shift, look_forward=look_forward, batch_size=batch_size)
    test_feature = DataPreprocessor.time_shift_transform(test_data, time_shift=time_shift, look_forward=look_forward)
    test_feature = test_feature[-batch_size:]
    model = Sequential()
    model.add(LSTM(100, input_shape=(train_feature.shape[1], train_feature.shape[2]), stateful=True, batch_size=batch_size))
    model.add(Dense(1, batch_size=batch_size))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(train_feature, train_target, epochs=20, batch_size=batch_size, verbose=2)
    result = model.predict(test_feature, batch_size=batch_size)
    if all_result is None:
        all_result = result[-1,:]
    else:
        all_result = numpy.concatenate((all_result, result[-1,:]))

all_result = scalar.inverse_transform(all_result.reshape(-1,1))
all_result = numpy.pad(all_result, (train_size, 0), "constant", constant_values=numpy.nan)

plt.plot(unscaled)
plt.plot(all_result)
plt.show()
#
# prediction = model.predict(train_feature, batch_size=batch_size)
# train_prediction = scalar.inverse_transform(train_prediction).flatten()
# test_prediction = scalar.inverse_transform(test_prediction).flatten()
# full_data = scalar.inverse_transform(full_data)
#
# if graph_time_shift:
#     train_prediction = numpy.pad(train_prediction, (time_shift + look_forward, 0), "constant", constant_values=numpy.nan)
#     test_prediction = numpy.pad(test_prediction, (train_size + time_shift + look_forward, 0), "constant", constant_values=numpy.nan)
# else:
#     test_prediction = numpy.pad(test_prediction, (train_size + time_shift + look_forward, 0), "constant", constant_values=numpy.nan)
#
# plt.plot(full_data, label='Original')
# plt.plot(train_prediction, label='Train')
# plt.plot(test_prediction, label='Test')
# plt.legend()
# plt.show()