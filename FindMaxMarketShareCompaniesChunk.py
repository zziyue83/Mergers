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
            brandsVolume = pd.concat([brandsVolume,data_chunk.groupby(['month','brand_descr']).agg({'volume': 'sum'})])
        brandsVolume = brandsVolume.groupby(level=[0,1]).agg({'volume': 'sum'})
        top100forEachMonth = brandsVolume.groupby(level=0)['volume'].nlargest(100)
        brandsCumuYear.extend(list(set(top100forEachMonth.index.get_level_values(2))))
        print(len(brandsCumuYear))
        
    brands_descr = list(set(brandsCumuYear))
    dict = {'brand_descr': brands_descr}
    topBrandDf = pd.DataFrame(dict)
    print(topBrandDf)
    print(len(topBrandDf))
    topBrandDf.to_csv('Top 100 '+product+'.csv')

if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
years = GenerateYearList(start, end)
print(years)
MarketShare(product, years)
