import math
import matplotlib.pyplot as plt
from rnn.data_preprocessor import DataPreprocessor
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
import numpy


time_shift = 5
look_forward = 1
batch_size = 5
data_count = 1000
data_arr = []
for x in range(0, data_count + time_shift + look_forward):
    data_arr.append(math.sin(x * math.pi / 180))
scalar = MinMaxScaler()
scaled_data = scalar.fit_transform(numpy.array(data_arr).reshape(-1, 1))
processor = DataPreprocessor(scaled_data)
processor.add_feature(scaled_data)
train_feature, train_target = processor.build(time_shift=time_shift, look_forward=look_forward, batch_size=batch_size)

model = Sequential()
model.add(LSTM(100, input_shape=(train_feature.shape[1], train_feature.shape[2]), stateful=True, batch_size=batch_size))
model.add(Dense(1, batch_size=time_shift))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(train_feature, train_target, epochs=10, batch_size=batch_size, verbose=2)

train_predict = model.predict(train_feature, batch_size=batch_size)
test_predict = train_predict[-(time_shift + look_forward + batch_size):]
train_predict = scalar.inverse_transform(train_predict)
count = 0
while count < 100:
    test_feature = DataPreprocessor.time_shift_transform(test_predict, time_shift=time_shift, look_forward=look_forward, batch_size=5)
    result = model.predict(test_feature, batch_size=batch_size)
    print(result.shape)
    test_predict = numpy.concatenate((test_predict, result[-batch_size:,:]))
    count += 1
test_predict = test_predict[time_shift + look_forward + batch_size:]
test_predict = scalar.inverse_transform(test_predict)
plt.plot(data_arr, label="Full data")
plt.plot(numpy.pad(train_predict, (time_shift + look_forward, 0), "constant", constant_values=numpy.nan), label="Train")
plt.plot(numpy.pad(test_predict, (len(train_predict), 0), "constant", constant_values=numpy.nan))
plt.legend(loc='upper right')
plt.show()