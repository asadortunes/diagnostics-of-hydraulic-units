import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(data):
    data = data.copy()
    columns = data.columns

    for column in columns:
        series = data[column]
        features = pd.DataFrame({
            'values': series,
            'diff_1': series.diff(),
            'diff_5': series.diff(5),
            'rolling_mean': series.shift(1).rolling(5).mean(),
            'rolling_std': series.shift(1).rolling(5).std()

        })

        valid = features.notna().all(axis=1)

        model = IsolationForest(
            n_estimators=300,
            max_samples=256,
            contamination=0.0065,
            max_features=1.0,
            random_state=17
        )

        model.fit(features.loc[valid])
        predict = model.predict(features.loc[valid])
        anomaly = pd.Series(0, index=data.index)
        anomaly.loc[valid] = (predict == -1).astype(int)

        data[column + '_anomaly'] = anomaly

    return data