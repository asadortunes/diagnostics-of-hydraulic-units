from utils.preprocessing import load_data, preprocessing
from methods.quantiles.detector import detect_anomalies as detect_quantiles
from methods.range.detector import detect_anomalies as detect_range
from methods.isolation_forest.detector import detect_anomalies as detect_isolation_forest


data = load_data("data/train.csv")
data = preprocessing(data)

#Должно появиться поле, в котором вводить диапазоны значений
Oil_min = float(input())
Oil_max = float(input())

Bearing_min = float(input())
Bearing_max = float(input())

Vibration_min = float(input())
Vibration_max = float(input())

RMP_min = float(input())
RMP_max = float(input())

Power_min = float(input())
Power_max = float(input())

Water_flow_min = float(input())
Water_flow_max = float(input())
ranges = [[Oil_min, Oil_max], [Bearing_min, Bearing_max], [Vibration_min, Vibration_max], [RMP_min, RMP_max], [Power_min, Power_max], [Water_flow_min, Water_flow_max]]


#Нужно сделать чтобы запускался только тот метод, который выбрал пользователь
print("Запуск метода квантилей...")
quantiles_results = detect_quantiles(data)
quantiles_results.to_csv("results/data_results.csv")

print("Запуск метода диапазона...")
range_results = detect_range(data, ranges)
range_results.to_csv("results/data_results.csv")

print("Запуск Isolation Forest...")
isolation_results = detect_isolation_forest(data)
isolation_results.to_csv("results/data_results.csv")
