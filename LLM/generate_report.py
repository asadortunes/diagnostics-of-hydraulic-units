import os
import json
import pandas as pd
from utils.preprocessing import preprocessing


def generate_json(input_file: str, output_file: str) -> dict:
    data = pd.read_csv(input_file)
    data = preprocessing(data)

    anomaly_columns = [c for c in data.columns if c.endswith("_anomaly")]
    anomalies_lst = []

    for column in anomaly_columns:
        sensor = column[:-len("_anomaly")]
        flagged = data.index[data[column].astype(bool).to_numpy()]

        if len(flagged) == 0:
            continue

        start_time = flagged[0]
        end_time = flagged[0]

        for time in flagged[1:]:
            if time - end_time == pd.Timedelta("1min"):
                end_time = time
            else:
                anomalies_lst.append(
                    {"sensor": sensor,
                     "start_time": str(start_time),
                     "end_time": str(end_time)}
                )
                start_time = time
                end_time = time

        anomalies_lst.append(
            {"sensor": sensor,
             "start_time": str(start_time),
             "end_time": str(end_time)}
        )

    report = {"total_anomalies": len(anomalies_lst), "anomalies": anomalies_lst}

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

    return report