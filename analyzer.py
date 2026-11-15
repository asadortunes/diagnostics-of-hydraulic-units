import pandas as pd
import pickle
import json

data = pd.read_csv('train.csv')
data['Timestamp'] = pd.to_datetime(data['Timestamp'])
data = data.sort_values('Timestamp').reset_index(drop=True)

features = ['Oil_Pressure_Bar', 'Bearing_Temp_C', 'Vibration_mm_s',
            'RPM', 'Active_Power_MW', 'Water_Flow_m3_h']
X = data[features]

with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

data['score'] = model.decision_function(X)
data['is_anomaly'] = (model.predict(X) == -1).astype(int)

# нормальное значение каждого датчика (медиана на обучающей выборке)
baseline = pd.Series({
    'Oil_Pressure_Bar': 4.2,
    'Bearing_Temp_C': 65.5,
    'Vibration_mm_s': 1.9,
    'RPM': 3000.0,
    'Active_Power_MW': 150.5,
    'Water_Flow_m3_h': 1199.95,
})

# вклад датчика: на сколько вырастет score, если заменить датчик на норму
gain = pd.DataFrame(index=data.index)
for f in features:
    X2 = X.copy()
    X2[f] = baseline[f]
    gain[f] = model.decision_function(X2) - model.decision_function(X)

# склеиваем срабатывания в периоды
def make_episodes(times, max_gap=20, min_len=3):
    if len(times) == 0:
        return []

    episodes = []
    group = [times[0]]
    for t in times[1:]:
        if t - group[-1] <= pd.Timedelta(minutes=max_gap):
            group.append(t)
        else:
            if len(group) >= min_len:
                episodes.append((group[0], group[-1]))
            group = [t]
    if len(group) >= min_len:
        episodes.append((group[0], group[-1]))
    return episodes

times = data.loc[data['is_anomaly'] == 1, 'Timestamp'].tolist()
episodes = make_episodes(times)

# период, где датчики и флаг 1 на всех минутах периода
data['if_period'] = 0
result = []

for start, end in episodes:
    in_period = data['Timestamp'].between(start, end)
    flagged = in_period & (data['is_anomaly'] == 1)

    data.loc[in_period, 'if_period'] = 1
    sensors = gain[flagged].idxmax(axis=1).value_counts().index.tolist()

    result.append({'start': str(start), 'end': str(end),
                   'sensors': sensors, 'flagged_minutes': int(flagged.sum())})

# участки по датчикам внутри периода
timeline = []

for start, end in episodes:
    in_period = data['Timestamp'].between(start, end)
    top = gain[in_period].idxmax(axis=1)

    last = None
    for t, sensor in zip(data.loc[in_period, 'Timestamp'], top):
        if last is not None and last['sensor'] == sensor:
            last['end'] = str(t)
        else:
            last = {'sensor': sensor, 'start': str(t), 'end': str(t)}
            timeline.append(last)

# сохранение
data[['Timestamp', 'score', 'is_anomaly', 'if_period']].to_csv('minutes_if.csv', index=False)

with open('anomalies_if.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

with open('timeline_if.json', 'w') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)