import pandas as pd
import sys
import numpy as np
import pyblp

def GenerateDEData(products, quarterOrMonth, inputs, characteristics):
    data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_estimation.tsv", delimiter = '\t')
    variables = ['dma_code_' + quarterOrMonth,'upc_dma_code','log_adjusted_price','upc','market_share','distance','time'] + products + inputs + characteristics
    demand_estimation_data = data[variables]
    demand_estimation_data = demand_estimation_data.dropna()
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_' + quarterOrMonth:'market_ids','log_adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids','upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    
    # Plain Logit
    logit_formulation = pyblp.Formulation('0 + prices + mint + chocolate', absorb = 'C(upc_dma_code) + C(time)')
    
    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)
    resultDf = pd.DataFrame.from_dict(data=logit_results.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/' + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_plain_logit1.csv', sep = ',')
    
    # Nested Logit
    demand_estimation_data['nesting_ids'] = 1
    groups = demand_estimation_data.groupby(['market_ids', 'nesting_ids'])
    demand_estimation_data['demand_instruments' + str(len(inputs)+1)] = groups['shares'].transform(np.size)
    
    nl_formulation = pyblp.Formulation('0 + prices + mint + chocolate', absorb = 'C(upc_dma_code) + C(time)')
    
    problem_nested = pyblp.Problem(nl_formulation, demand_estimation_data)
    nested_logit_results = problem_nested.solve(rho=0.7)
    print(nested_logit_results)
    resultDf_nested = pd.DataFrame.from_dict(data=nested_logit_results.to_dict(), orient='index')
    resultDf_nested.to_csv('RegressionResults/' + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_nested_logit1.csv', sep = ',')
    

quarterOrMonth = sys.argv[1]
#products = [sys.argv[2]]
#inputs = [sys.argv[3]]
#characteristics = [sys.argv[4]]
products = [sys.argv[2], sys.argv[3]]
inputs = [sys.argv[4], sys.argv[5]]
characteristics = [sys.argv[6], sys.argv[7]]
GenerateDEData(products, quarterOrMonth, inputs, characteristics)
