import pandas as pd
from tqdm import tqdm
products = pd.read_csv("../../GeneratedData/"+"CANDY"+"_dma_month_upc_"+"2009"+".tsv", header = 0, delimiter = "\t", index_col = "upc", chunksize = 100000)
brandsVolume = pd.DataFrame()
i = 0
for data_chunk in tqdm(products):
    if i == 2:
        break
    else:
        a = data_chunk
        i = i + 1

print(a[a['volume']=='volume'])
