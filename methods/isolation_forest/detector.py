from pandas.core.common import random_state
from sklearn.ensemble import IsolationForest


def detect_anomalies(data):
    data = data.copy()
    columns = data.columns

    for column in columns:
        model = IsolationForest(
            contamination=0.05,
            random_state=17
        )

        predict = model.fit_predict(data[column])
        anomaly = (predict == -1).astype(int)

        data[column + '_anomaly'] = anomaly

    return data