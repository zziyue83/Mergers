import pandas as pd
from tqdm import tqdm
products = pd.read_csv("../../GeneratedData/"+"CANDY"+"_dma_month_upc_"+"2009"+".tsv", header = 0, delimiter = "\t", index_col = "upc", chunksize = 10000001)
brandsVolume = pd.DataFrame()
i = 0
for data_chunk in tqdm(products):
    if i == 1:
        break
    else:
        print(data_chunk.iloc[0])
        i = i + 1

# print(a[a['volume']=='volume'])
