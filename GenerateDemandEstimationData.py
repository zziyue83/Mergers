import pandas as pd
import sys

def GenerateDEData(product, frequency):
    data = pd.read_csv("../../GeneratedData/" + product + "_pre_model_" + frequency + "_with_distance.tsv", delimiter = '\t')
    print(data)
    print(data.columns)
    print(data['market_share'])
    demand_estimation_data = data[['dma_code','log_adjusted_price','Firm','brand_descr',frequency+'_since_start','upc']]
    print(demand_estimation_data)
frequency = sys.argv[1]
product = sys.argv[2]
GenerateDEData(product, frequency)
