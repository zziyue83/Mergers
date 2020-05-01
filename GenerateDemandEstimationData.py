import pandas as pd

def GenerateDEData(products, frequency):
    data = pd.read_csv("../../GeneratedData/" + '_'.join([str(p) for p in products]) + "_pre_model_" + frequency + "_with_distance.tsv")
    print(data)
