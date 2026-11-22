from utils.preprocessing import load_data, preprocessing

from methods.quantiles.detector import detect_anomalies


# Загружаем данные
data = load_data("data/train.csv")

# Выполняем препроцессинг
data = preprocessing(data)


# Запускаем детекцию аномалий
results = detect_anomalies(data, "Bearing_Temp_C")


# Считаем количество аномалий
anomaly_count = results.sum()

print("Количество аномалий:", anomaly_count)

print("\nНайденные аномалии:")

print(data[results == 1])
