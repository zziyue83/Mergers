import pandas as pd
import sys
import numpy as np
import pyblp
log = open("RegressionResults/plain_candy_gum_nestedshare.log", "a")
sys.stdout = log

def GenerateDEData(products, quarterOrMonth, inputs):
    data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_estimation.tsv", delimiter = '\t')
    total_share = data.groupby(['dma_code_' + quarterOrMonth]).agg({'market_share':'sum'})
    data['total_share'] = data['dma_code_' + quarterOrMonth].map(total_share['market_share'])
    data['nestedshare'] = np.log(data['market_share']/data['total_share'])
    data = data[data['postmerger'] == 0]
    variables = ['dma_code_' + quarterOrMonth,'dma_code','owner initial','brand_descr','adjusted_price','upc','market_share','distance','time','nestedshare'] + inputs
    demand_estimation_data = data[variables]
    demand_estimation_data = demand_estimation_data.dropna()
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_' + quarterOrMonth:'market_ids','dma_code':'city_ids','adjusted_price':'prices','owner initial':'firm_ids','brand_descr':'brand_ids','upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    
    # Plain Logit
    logit_formulation = pyblp.Formulation('0 + prices + time + nestedshare', absorb = 'C(product_ids) + C(city_ids)')
    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)
    resultDf = pd.DataFrame.from_dict(data=logit_results.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/' + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_plain_logit_nestedshare.csv', sep = ',')

quarterOrMonth = sys.argv[1]
products = [sys.argv[2], sys.argv[3]]
inputs = [sys.argv[4], sys.argv[5]]
GenerateDEData(products, quarterOrMonth, inputs)
