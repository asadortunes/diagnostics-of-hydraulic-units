import pandas as pd
import numpy as np


def detect_anomalies(data, data_clear):
    data = data.copy()
    columns = data.columns

    for column in columns:
        x = data[column]
        mean = data_clear[column].mean()
        std = data_clear[column].std()
        z = (x - mean) / std

        anomaly = z.abs() > 3.5
        near = anomaly.rolling(5, center=True, min_periods=1).sum() >= 2
        edge = anomaly.shift(1, fill_value=False) | anomaly.shift(-1, fill_value=False)

        anomaly = anomaly | (edge & near)
        data[column + '+anomaly'] = anomaly.astype(int)

    return data
