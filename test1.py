import pandas as pd
products = ['CANDY','GUM']
quarterOrMonth = 'month'
data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_estimation.tsv", delimiter = '\t')
print(len(data))
