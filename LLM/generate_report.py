import pandas as pd
import json
from utils.preprocessing import preprocessing


def generate_json(input_file, output_file):
    data = pd.read_csv(input_file)
    data = preprocessing(data)
    anomaly_columns = [column for column in data.columns if '_anomaly' in column]
    anomalies_lst = []

    for column in anomaly_columns:
        sensor = column.replace('_anomaly', '')
        anomalies_times = data[data[column] == 1].index.to_list()
        if len(anomalies_times) == 0:
            continue
        start_time = anomalies_times[0]
        end_time = anomalies_times[0]

        for time in anomalies_times[1:]:
            if time - end_time == pd.Timedelta('1min'):
                end_time = time
            else:
                anomalies_lst.append({
                    'sensor': sensor,
                    'start_time': str(start_time),
                    'end_time': str(end_time)})

                start_time = time
                end_time = time

        anomalies_lst.append({
            'sensor': sensor,
            'start_time': str(start_time),
            'end_time': str(end_time)})

    report = {'total_anomalies': len(anomalies_lst), 'anomalies': anomalies_lst}

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(report, file, ensure_ascii=False, indent=4)



generate_json("../results/data_results.csv","../results/anomaly_report.json")



