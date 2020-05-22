import pandas as pd
import sys
import numpy as np
import pyblp

def GenerateDEData(products, quarterOrMonth, inputs, characteristics):
    data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_estimation.tsv", delimiter = '\t')
    data = data[data['postmerger'] == 0]
    variables = ['dma_code_' + quarterOrMonth,'dma_code','owner initial','brand_descr','adjusted_price','upc','market_share','distance','time'] + inputs
    demand_estimation_data = data[variables]
    demand_estimation_data = demand_estimation_data.dropna()
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_' + quarterOrMonth:'market_ids','dma_code':'city_ids','adjusted_price':'prices','owner initial':'firm_ids','brand_descr':'brand_ids','upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)

    # Nested Logit
    demand_estimation_data['nesting_ids'] = 1
    groups = demand_estimation_data.groupby(['market_ids', 'nesting_ids'])
    demand_estimation_data['demand_instruments' + str(len(inputs)+1)] = groups['shares'].transform(np.size)
    
    nl_formulation = pyblp.Formulation('0 + prices + time', absorb = 'C(product_ids) + C(city_ids)')
    
    problem_nested = pyblp.Problem(nl_formulation, demand_estimation_data)
    nested_logit_results = problem_nested.solve(rho=0.7)
    print(nested_logit_results)
    resultDf_nested = pd.DataFrame.from_dict(data=nested_logit_results.to_dict(), orient='index')
    resultDf_nested.to_csv('RegressionResults/' + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_nested_logit.csv', sep = ',')

quarterOrMonth = sys.argv[1]
#products = [sys.argv[2]]
#inputs = [sys.argv[3]]
#characteristics = [sys.argv[4]]
products = [sys.argv[2], sys.argv[3]]
inputs = [sys.argv[4], sys.argv[5]]
characteristics = [sys.argv[6], sys.argv[7]]
GenerateDEData(products, quarterOrMonth, inputs, characteristics)
