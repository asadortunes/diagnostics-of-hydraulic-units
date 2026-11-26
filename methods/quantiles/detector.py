import pandas as pd


def detect_anomalies(data):
    data = data.copy()
    columns = [c for c in data.select_dtypes('number').columns
               if not c.endswith('_anomaly')]

    for column in columns:
        q1 = data[column].quantile(0.1)
        q3 = data[column].quantile(0.9)
        iqr = max(q3 - q1, 0.2)

        lower_bound = q1 - 1.0 * iqr
        upper_bound = q3 + 1.0 * iqr

        anomalies = (data[column] < lower_bound) | (data[column] > upper_bound)
        data[column + '_anomaly'] = anomalies.astype(int)

    return data