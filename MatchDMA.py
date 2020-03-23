import pandas as pd
from major_us_city_dma_codes import major_cities

movement = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv", delimiter = '\t' , index_col = "upc" , chunksize = 1000000)
dmaDf = pd.DataFrame(major_cities)
citydma = dmaDf['dma_code'].tolist()
movementdma = movement['dma_code'].unique()
for dma in movementdma:
    if dma not in citydma:
        print(dma)
