import pandas as pd
from tqdm import tqdm
import sys

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def AddExtraFeatures(product, years):
    years = list(map(str,years))
    brandsCumuYear = []
    for year in years:
        firstFile = True
        savePath = "../../GeneratedData/"+product+"_dma_month_upc_"+year+"_with_features.tsv"
        movement = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv", delimiter = '\t' , index_col = "upc" , chunksize = 1000000)
        features = pd.read_csv("../../Data/nielsen_extracts/RMS/"+year+"/Annual_Files/products_extra_"+year+".tsv", delimiter = '\t', index_col = 'upc')
        for data_chunk in tqdm(movement):
            merged = data_chunk.merge(features, how = 'left', left_index = True, right_index = True)
            if firstFile:
                merged.to_csv(savePath, sep = '\t')
                firstFile = False
            else:
                merged.to_csv(savePath, sep = '\t', header = False, mode = 'a')


if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
years = GenerateYearList(start, end)
print(years)
AddExtraFeatures(product, years)
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91
