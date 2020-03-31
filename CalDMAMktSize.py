import pandas as pd
from tqdm import tqdm
import sys

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def CalDMAMktSize(product, years, size_multiplier, frequency):
    area_quarter_mkt_list = []
    years = list(map(str,years))
    aggregation_function = {'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first','sales':'sum', 'volume':'sum','brand_descr':'first','brand_code_uc':'first','multi':'first','size1_amount':'first'}
    for year in years:
        firstFile = True
        movement = pd.read_csv("../../GeneratedData/"+product+"_dma_"+frequency+"_upc_"+year+".tsv", delimiter = '\t', chunksize = 100000)
        for data_chunk in tqdm(movement):
            area_quarter = data_chunk.groupby([frequency,'dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
            area_quarter = area_quarter[[frequency,'dma_code','volume']]
            area_quarter['volume'] = area_quarter['volume'] * size_multiplier
            area_quarter_mkt_list.append(area_quarter)

    area_quarter_agg = pd.concat(area_quarter_mkt_list)
    area_quarter_agg = pd.groupby([frequency,'dma_code'], as_index = False).aggregate({'volume':'sum'}).reindex(columns = data_chunk.columns)

    savePath = "../../GeneratedData/"+product+"_dma_"+frequency+"_mkt_size.tsv"
    mkt_size_agg_function = {'volume': 'max', frequency:'first'}
    dmaGroup = area_quarter_agg.groupby(['dma_code'], as_index = False)
    example = dmaGroup.get_group(592)
    print(example)
    print(example[frequency])
    area_quarter_agg = dmaGroup.aggregate(mkt_size_agg_function).reindex(columns = area_quarter_agg.columns)
    area_quarter_agg.drop([frequency], axis=1, inplace=True)
    area_quarter_agg = area_quarter_agg.rename(columns = {'dma_code':'dma_code','volume':'mkt_size'})
    area_quarter_agg = area_quarter_agg.set_index('dma_code')
    print(area_quarter_agg)
    area_quarter_agg.to_csv(savePath, sep = '\t', encoding = 'utf-8')
            #     firstFile = False
            #     print(area_quarter.iloc[0])
            # else:
            #     area_quarter.to_csv(savePath, sep = '\t', encoding = 'utf-8', mode = 'a', header = False)



if len(sys.argv) < 5:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
frequency = sys.argv[4]
years = GenerateYearList(start, end)
print(product)
print(years)
CalDMAMktSize(product, years, 1.5, frequency)
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91'
