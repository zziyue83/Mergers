import pandas as pd
from major_us_city_dma_codes import major_cities

movement = pd.read_csv("../../GeneratedData/BEER_dma_month_upc_2006.tsv", delimiter = '\t' , index_col = "upc" , chunksize = 1000000)
dmaDf = pd.DataFrame(major_cities)
citydma = dmaDf['dma_code'].tolist()
movementdma = movement['dma_code'].unique()
for dma in movementdma:
    if dma not in citydma:
        print(dma)
