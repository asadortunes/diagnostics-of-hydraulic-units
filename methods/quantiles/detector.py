import pandas as pd


def detect_anomalies(data, column):
    q1 = data[column].quantile(0.25)
    q3 = data[column].quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    anomalies = (data[column] < lower_bound) | (data[column] > upper_bound)
    anomalies = anomalies.astype('int')

    return anomalies