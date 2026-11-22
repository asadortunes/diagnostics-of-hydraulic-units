def detect_anomalies(data, ranges):
    data = data.copy()
    columns = data.columns

    for i, col in enumerate(columns):
        r = ranges[i]
        data[col + '_anomaly'] = ((data[col] > r[1]) | (data[col] < r[0])).astype(int)

    return data

