from utils.preprocessing import load_data, preprocessing


data = load_data('../data/train.csv')
data = preprocessing(data)