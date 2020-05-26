import pyblp
import sys
import numpy as np
import pandas as pd

log = open("rc_logit_sample_with_demographics.log", "a")
sys.stdout = log

def GenerateDEData(products, quarterOrMonth, inputs, characteristics):
    data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_estimation.tsv", delimiter = '\t')
    random_subset = data.sample(frac=0.05)
    random_subset = random_subset[random_subset['postmerger'] == 0]
    variables = ['dma_code_' + quarterOrMonth,'dma_code','owner initial','brand_descr','adjusted_price','upc','market_share','distance','time'] + inputs + characteristics
    demand_estimation_data = random_subset[variables]
    demand_estimation_data = demand_estimation_data.dropna()
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_' + quarterOrMonth:'market_ids','dma_code':'city_ids','adjusted_price':'prices','owner initial':'firm_ids','brand_descr':'brand_ids','upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    
    #random coeffcient logit regression
    x2formulation = '1 + prices'
    for characteristic in characteristics:
        x2formulation = x2formulation + ' + '+ characteristic
    print(x2formulation)

    X1_formulation = pyblp.Formulation('0 + prices + time', absorb='C(product_ids)+C(city_ids)')
    X2_formulation = pyblp.Formulation(x2formulation)
    product_formulations = (X1_formulation, X2_formulation)
    grid_integration = pyblp.Integration('grid', size=7)
    
    # adding demographics
    agent_data = pd.read_csv('Clean/agent_date.csv',delimiter = ',')
    agent_data['market_ids'] = agent_data['dma_code'].astype(str) + ' ' + agent_data[quarterOrMonth].astype(str)
    agent_formulation = pyblp.Formulation('0 + HINCP + AGEP + RAC1P')
    
    grid_problem = pyblp.Problem(product_formulations, demand_estimation_data, agent_formulation, agent_data, integration=grid_integration)
    print(grid_problem)
    bfgs = pyblp.Optimization('bfgs', {'gtol': 1e-10})
    
    dim = 2 + len(characteristics)
    print(dim)
    
    results1 = grid_problem.solve(sigma=np.ones((dim, dim)), optimization=bfgs)
    print(results1)
    resultDf1 = pd.DataFrame.from_dict(data=results1.to_dict(), orient='index')
    resultDf1.to_csv('RegressionResults/test_' + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_rc_logit_grid_ones_5%_with_demographics.csv', sep = ',')
    
    results2 = grid_problem.solve(sigma=np.eye(dim), optimization=bfgs)
    print(results2)
    resultDf2 = pd.DataFrame.from_dict(data=results2.to_dict(), orient='index')
    resultDf2.to_csv('RegressionResults/test_' + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_rc_logit_grid_diagonal_5%_with_demographics.csv', sep = ',')

quarterOrMonth = sys.argv[1]
products = [sys.argv[2], sys.argv[3]]
inputs = [sys.argv[4], sys.argv[5]]
characteristics = [sys.argv[6], sys.argv[7]]
GenerateDEData(products, quarterOrMonth, inputs, characteristics)