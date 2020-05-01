import pandas as pd
import sys
import pyblp

def GenerateDEData(product, frequency):
    data = pd.read_csv("../../GeneratedData/" + product + "_pre_model_" + frequency + "_with_distance.tsv", delimiter = '\t')
    data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    demand_estimation_data = data[['dma_code_'+frequency,'log_adjusted_price','upc','market_share','distance']]
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_'+frequency:'market_ids','log_adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    print(demand_estimation_data.head())
    pyblp.options.collinear_atol = pyblp.options.collinear_rtol = 0
    logit_formulation = pyblp.Formulation('prices')
    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)


frequency = sys.argv[1]
product = sys.argv[2]
GenerateDEData(product, frequency)
