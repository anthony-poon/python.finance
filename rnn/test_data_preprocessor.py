from unittest import TestCase
from rnn.data_preprocessor import DataPreprocessor
import pprint
import numpy.testing

class TestDataPreprocessor(TestCase):
    def test_build(self):
        time_shift = 3
        look_forward = 1
        data = []
        data.append([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        data.append([20, 30, 40, 50, 60, 70, 80, 90, 100, 110])
        processor = DataPreprocessor(data[0])
        processor.add_feature(data[0])
        processor.add_feature(data[1])
        feature, sample = processor.build(time_shift=time_shift, look_forward=look_forward)
        for sample_index in range(0, feature.shape[0]):
            for feature_index in range(0, 2):
                print("{0}".format(feature[sample_index, :, feature_index]), sample[sample_index])
                numpy.testing.assert_allclose(feature[sample_index, :, feature_index], data[feature_index][sample_index:sample_index + time_shift])
                numpy.testing.assert_allclose(sample[sample_index], data[0][sample_index + time_shift + look_forward - 1:sample_index + time_shift + look_forward])
        print("OK")

    def test_batch_size_test(self):
        time_shift = 3
        look_forward = 1
        batch_size = 2
        data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        processor = DataPreprocessor(data)
        processor.add_feature(data)
        feature, sample = processor.build(time_shift=time_shift, look_forward=look_forward, batch_size=batch_size)
        for x in range(0, feature.shape[0]):
            print(feature[x, :, 0])
        # nb_sample = nb_data_pt - time_shift - look_forward + 1
        nb_sample = len(data) - time_shift - look_forward + 1
        self.assertEqual(feature.shape[0], nb_sample - (nb_sample % batch_size))
        self.assertEqual(len(sample), len(sample) - (len(sample) % batch_size))