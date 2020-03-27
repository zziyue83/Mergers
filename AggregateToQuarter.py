import pandas as pd
from tqdm import tqdm
import sys

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def AggregateToQuarter(product, years):
    years = list(map(str,years))
    brandsCumuYear = []
    aggregation_function = {'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first','sales':'sum', 'volume':'sum'}
    for year in years:
        firstFile = True
        savePath = "../../GeneratedData/"+product+"_dma_quarter_upc_"+year+".tsv"
        movement = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv", delimiter = '\t' , index_col = "upc" , chunksize = 1000000)
        for data_chunk in tqdm(movement):
            data_chunk['quarter'] = pd.to_datetime(data_chunk['month'].values, format = '%Y%m').astype('period[Q]')
            area_quarter_upc = data_chunk.groupby(['quarter', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
            if firstFile:
                area_quarter_upc.to_csv(savePath, sep = '\t', encoding = 'utf-8')
                firstFile = False
                print(area_quarter_upc.iloc[0])
            else:
                area_quarter_upc.to_csv(savePath, sep = '\t', encoding = 'utf-8', mode = 'a', header = False)



if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
years = GenerateYearList(start, end)
print(product)
print(years)
AggregateToQuarter(product, years)
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91'
