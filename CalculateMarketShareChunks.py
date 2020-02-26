import pandas as pd
import sys
from tqdm import tqdm

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def MarketShare(product, years):
    years = list(map(str,years))
    brandsCumuYear = []
    for year in years:
        productsTable = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv", delimiter = "\t", index_col = "upc", chunksize = 1000000)
        brandsVolume = pd.DataFrame()
        for data_chunk in tqdm(productsTable):
            data_chunk.volume = data_chunk.volume.astype('float64')
            brandsVolume = pd.concat([brandsVolume,data_chunk.groupby(['month','brand_code_uc']).agg({'volume': 'sum'})])
        brandsVolume = brandsVolume.groupby(level=[0,1]).agg({'volume': 'sum'})
        top100forEachMonth = brandsVolume.groupby(level=0)['volume'].nlargest(100)
        brandsCumuYear.extend(list(set(top100forEachMonth.index.get_level_values(2))))
        print('brandsCumuYear' + str(len(brandsCumuYear)))
        
    brands = list(set(brandsCumuYear))
    print(len(brands))
    print(brands)    
    return brands

if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
years = GenerateYearList(start, end)
print(years)
MarketShare(product, years)
