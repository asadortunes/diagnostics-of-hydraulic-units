import pandas as pd

def load_data(file_path):
    data = pd.read_csv(file_path)
    return data


def preprocessing(data):
    data = data.copy()
    data['Timestamp'] = pd.to_datetime(data['Timestamp'])
    data = data.dropna(subset=['Timestamp'])
    data = data.drop_duplicates()
    data = data.set_index('Timestamp')
    data = data.sort_index()

    for column in data.columns:
        data[column] = data[column].fillna(
            (data[column].shift(1) + data[column].shift(2)) / 2
        )
    data = data.dropna()

    return data