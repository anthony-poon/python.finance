import numpy


class DataPreprocessor:
    def __init__(self, label):
        # reshape to single column
        self._label = label
        self._feature = []

    @staticmethod
    def time_shift_transform(*array_like, time_shift=1, look_forward=5, batch_size=1):
        feature_matrix = numpy.empty((len(array_like[0]) - time_shift - look_forward + 1, time_shift, len(array_like)))
        for sample_index in range(0, len(array_like[0]) - time_shift - look_forward + 1):
            for feature_index in range(0, len(array_like)):
                for time_index in range(0, time_shift):
                    feature_matrix[sample_index][time_index][feature_index] = array_like[feature_index][sample_index + time_index]
        if batch_size > 1:
            reminder = len(feature_matrix) % batch_size
            if reminder > 0:
                feature_matrix = feature_matrix[0:-reminder, :, :]
        return feature_matrix

    def add_feature(self, feature):
        self._feature.append(feature)

    def build(self, time_shift=1, look_forward=5, batch_size=1):
        feature_matrix = self.time_shift_transform(*self._feature, time_shift=time_shift, look_forward=look_forward, batch_size=batch_size)
        feature_matrix = numpy.array(feature_matrix)
        label_matrix = numpy.array(self._label[time_shift + look_forward - 1:]).reshape(-1, 1)
        if batch_size > 1:
            reminder = len(label_matrix) % batch_size
            if reminder > 0:
                label_matrix = label_matrix[0:-reminder]
        return feature_matrix, label_matrix