import pandas as pd
import sys
import numpy as np
import pyblp

def GenerateDEData(products, quarterOrMonth, inputs, characteristics):
    datachunks = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_estimation.tsv", delimiter = '\t',chunksize = 100000)
    for df in datachunks:
        data = df
        break
    data = data[data['postmerger'] == 0]
    variables = ['dma_code_' + quarterOrMonth,'dma_code','owner initial','log_adjusted_price','upc','market_share','distance'] + inputs + characteristics
    demand_estimation_data = data[variables]
    print(demand_estimation_data)
    # a = demand_estimation_data[demand_estimation_data.isnull()]
    # print(a)
    # print(a.iloc[0])
    demand_estimation_data = demand_estimation_data.dropna()
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_' + quarterOrMonth:'market_ids','dma_code':'city_ids','log_adjusted_price':'prices','owner initial':'firm_ids','brand_descr':'brand_ids','upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)

    # Plain Logit
    logit_formulation = pyblp.Formulation('0 + prices + mint + chocolate', absorb = 'C(product_ids) + C(city_ids) + C(market_ids)')

    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)
    resultDf = pd.DataFrame.from_dict(data=logit_results.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/' + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_plain_logit.csv', sep = ',')

quarterOrMonth = sys.argv[1]
#products = [sys.argv[2]]
#inputs = [sys.argv[3]]
#characteristics = [sys.argv[4]]
products = [sys.argv[2], sys.argv[3]]
inputs = [sys.argv[4], sys.argv[5]]
characteristics = [sys.argv[6], sys.argv[7]]
GenerateDEData(products, quarterOrMonth, inputs, characteristics)
