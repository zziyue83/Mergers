import pandas as pd

def ShareInfo(product,frequency):
    data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
    print(data.columns)
    print(data.head())

ShareInfo('BEER','month')
