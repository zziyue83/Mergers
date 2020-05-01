import pandas as pd
import sys

def GenerateDEData(product, frequency):
    data = pd.read_csv("../../GeneratedData/" + product + "_pre_model_" + frequency + "_with_distance.tsv", delimiter = '\t')
    print(data)
    print(data.columns)
    print(data['market_share'])
    demand_estimation_data = data[['dma_code','log_adjusted_price','Firm','brand_descr',frequency+'_since_start','upc','market_share']]
    print(demand_estimation_data)
    rename_dic = {'dma_code':'market_ids','log_adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    print(demand_estimation_data.head())


frequency = sys.argv[1]
product = sys.argv[2]
GenerateDEData(product, frequency)
