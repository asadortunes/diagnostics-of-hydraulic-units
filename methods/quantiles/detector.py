import pandas as pd


def detect_anomalies(data):
    data = data.copy()
    columns = data.columns

    for column in columns:
        q1 = data[column].quantile(0.1)
        q3 = data[column].quantile(0.9)
        iqr = max(q3 - q1, 0.2)

        lower_bound = q1 - 1.0 * iqr
        upper_bound = q3 + 1.0 * iqr

        anomalies = (data[column] < lower_bound) | (data[column] > upper_bound)
        data[column + '_anomaly'] = anomalies

    return data