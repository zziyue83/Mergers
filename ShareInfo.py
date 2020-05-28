import pandas as pd

data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
print(data.head())
