import pandas as pd
import sys
import pyblp
import numpy as np
from tqdm import tqdm

# def RCLogit(product, frequency, inputs, characteristics, start, end):
#     log = open("random_coefficient_logit_regression.log", "a")
#     sys.stdout = log
#     data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
#     data['y-m'] = pd.to_datetime(data['y-m-d']).dt.to_period('M')
#     data['year'] = pd.to_datetime(data['y-m-d']).dt.to_period('Y')
#     data['year'] = data['year'].astype(str)
#     data = data[data['postmerger'] == 0]
#     years = GenerateYearList(start, end)
#     data = AddExtraFeatures(product, data, characteristics, years)
#     data = data.dropna()
#     print(data.shape)
#     print(data.columns)
#     for characteristic in characteristics:
#         if characteristic == 'style_descr':
#             data['style_descr'] = np.where(data['style_descr'] == 'DOMESTIC', 0, 1)
#     for input in inputs:
#         input_prices = ReadInstrument(input)
#         data = data.merge(input_prices, how = 'inner', left_on = 'y-m', right_on = 't')
#         data[input] = data[input] * data['price_index']
#         # print(data.head())
#     data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
#     # data['product_ids'] = data['upc'].astype(str) + '_' + data['dma_code'].astype(str)
#     variables = ['dma_code_'+frequency,'adjusted_price','market_share','y-m','upc','dma_code','owner initial','brand_descr','distance'] + characteristics + inputs
#     # variables = ['dma_code_'+frequency,'adjusted_price','market_share','distance','y-m','product_ids'] + characteristics + inputs
#     print(variables)
#     demand_estimation_data = data[variables]
#     print(demand_estimation_data.head())
#     rename_dic = {'dma_code_'+frequency:'market_ids','adjusted_price':'prices','upc':'product_ids','owner initial':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'distance':'demand_instruments0','market_share':'shares','y-m':'time','dma_code':'city_ids'}
#     for i in range(len(inputs)):
#         rename_dic[inputs[i]] = 'demand_instruments'+str(i)
#     demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
#     print(demand_estimation_data.head())
#
#     #random coeffcient logit regression
#     x2formulation = '1 + prices'
#     for characteristic in characteristics:
#         x2formulation = ' ' + x2formulation + '+ '+ characteristic
#
#     X1_formulation = pyblp.Formulation('0 + prices + time', absorb='C(product_ids)+C(city_ids)')
#     X2_formulation = pyblp.Formulation(x2formulation)
#     product_formulations = (X1_formulation, X2_formulation)
#
#     # mc_integration = pyblp.Integration('monte_carlo', size=50, specification_options={'seed': 0})
#     #
#     # pr_integration = pyblp.Integration('product', size=5)
#
#     grid_integration = pyblp.Integration('grid', size=7)
#
#     # mc_problem = pyblp.Problem(product_formulations, demand_estimation_data, integration=mc_integration)
#     # print(mc_problem)
#     # pr_problem = pyblp.Problem(product_formulations, demand_estimation_data, integration=pr_integration)
#     # print(pr_problem)
#     if not demographics:
#         grid_problem = pyblp.Problem(product_formulations, demand_estimation_data, integration=grid_integration)
#     else:
#         agent_data = pd.read_csv('Clean/agent_date.csv',delimiter = ',')
#         agent_data['market_ids'] = agent_data['dma_code'].astype(str)+agent_data[frequency].astype(str)
#         agent_formulation = pyblp.Formulation('0 + HINCP + AGEP + RAC1P')
#         grid_problem = pyblp.Problem(product_formulations, demand_estimation_data, agent_formulation, agent_data, integration=grid_integration)
#     print(grid_problem)
#
#     bfgs = pyblp.Optimization('bfgs', {'gtol': 1e-10})
#
#     # here 3 should be replaced by K2, which is printed above in mc_problem as linear demand estimators. For beer K2 is 3. using the identity matrix as covariance matrix
#     # results1 = mc_problem.solve(sigma=np.eye(3), optimization=bfgs)
#     # print(results1)
#     # resultDf = pd.DataFrame.from_dict(data=results1.to_dict(), orient='index')
#     # resultDf.to_csv('RegressionResults/test_'+product+'_rc_logit_monte_carlo.csv', sep = ',')
#     #
#     # results2 = pr_problem.solve(sigma=np.eye(3), optimization=bfgs)
#     # print(results2)
#     # resultDf = pd.DataFrame.from_dict(data=results2.to_dict(), orient='index')
#     # resultDf.to_csv('RegressionResults/test_'+product+'_rc_logit_product_rules.csv', sep = ',')
#
#     results = grid_problem.solve(sigma=np.eye(3), optimization=bfgs)
#     print(results)
#     resultDf = pd.DataFrame.from_dict(data=results.to_dict(), orient='index')
#     resultDf.to_csv('RegressionResults/test_'+product+'_rc_logit_grid.csv', sep = ',')

def SampleRCLogit(product, frequency, inputs, characteristics, start, end, demographics=False):
    try:
        log = open("one_iteration_random_coefficient_logit_regression_"+product+".log", "w")
        sys.stdout = log
        data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
        data['y-m'] = pd.to_datetime(data['y-m-d']).dt.to_period('M')
        data['year'] = pd.to_datetime(data['y-m-d']).dt.to_period('Y')
        data['year'] = data['year'].astype(str)
        data = data[data['postmerger'] == 0]
        years = GenerateYearList(start, end)
        data = AddExtraFeatures(product, data, characteristics, years)
        data = data.dropna()
        print(data.shape)
        print(data.columns)
        for characteristic in characteristics:
            if characteristic == 'style_descr':
                data['style_descr'] = np.where(data['style_descr'] == 'DOMESTIC', 0, 1)
        for input in inputs:
            input_prices = ReadInstrument(input)
            data = data.merge(input_prices, how = 'inner', left_on = 'y-m', right_on = 't')
            data[input] = data[input] * data['price_index']
            # print(data.head())
        data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
        # data['product_ids'] = data['upc'].astype(str) + '_' + data['dma_code'].astype(str)
        variables = ['dma_code_'+frequency,'adjusted_price','market_share','upc','dma_code','owner initial','brand_descr','distance',frequency+'_since_start'] + characteristics + inputs
        # variables = ['dma_code_'+frequency,'adjusted_price','market_share','distance','y-m','product_ids'] + characteristics + inputs

        print(variables)
        demand_estimation_data = data[variables]
        print(demand_estimation_data.head())
        rename_dic = {'dma_code_'+frequency:'market_ids','adjusted_price':'prices','upc':'product_ids','owner initial':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':'time','distance':'demand_instruments0','market_share':'shares','dma_code':'city_ids'}
        for i in range(len(inputs)):
            rename_dic[inputs[i]] = 'demand_instruments'+str(i)
        demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
        print(demand_estimation_data.head())

        #marktet_ids random sampling
        market_ids = demand_estimation_data['market_ids'].unique()
        np.random.seed(1000)
        sample = np.random.choice(market_ids,int(0.01*len(market_ids)),replace=False)
        print(sample)
        demand_estimation_data = demand_estimation_data[demand_estimation_data['market_ids'].isin(sample)]
        print(demand_estimation_data.head())


        #random coeffcient logit regression
        x2formulation = '1 + prices'
        for characteristic in characteristics:
            x2formulation = ' ' + x2formulation + '+ '+ characteristic

        X1_formulation = pyblp.Formulation('0 + prices + time', absorb='C(product_ids)+C(city_ids)')
        X2_formulation = pyblp.Formulation(x2formulation)
        product_formulations = (X1_formulation, X2_formulation)

        # mc_integration = pyblp.Integration('monte_carlo', size=50, specification_options={'seed': 0})
        #
        # pr_integration = pyblp.Integration('product', size=5)

        grid_integration = pyblp.Integration('grid', size=7)

        if not demographics:
            grid_problem = pyblp.Problem(product_formulations, demand_estimation_data, integration=grid_integration)
        else:
            agent_data = pd.read_csv('Clean/agent_date.csv',delimiter = ',')
            agent_data['market_ids'] = agent_data['dma_code'].astype(str)+agent_data[frequency].astype(str)
            agent_formulation = pyblp.Formulation('0 + HINCP + AGEP')
            grid_problem = pyblp.Problem(product_formulations, demand_estimation_data, agent_formulation, agent_data, integration=grid_integration)
        print(grid_problem)
        print('finished initializing the problem')
        bfgs = pyblp.Optimization('bfgs', {'gtol': 1e-10, 'maxiter' : 1})

        results = grid_problem.solve(sigma=np.eye(3), optimization=bfgs,method='1s')
        print(results)
        resultDf = pd.DataFrame.from_dict(data=results.to_dict(), orient='index')
        resultDf.to_csv('RegressionResults/'+product+'_rc_logit_sampling.csv', sep = ',')

    except Exception as error:
        print(error)

def ReadInstrument(input, skiprows = 0):
    instrument = pd.read_csv(input+'.csv', skiprows = skiprows, delimiter = ',')
    instrument['t'] = pd.to_datetime(instrument['time']).dt.to_period('M')
    instrument = instrument.groupby('t',as_index = False).agg({'price':'mean','time':'first'},as_index = False).reindex(columns = instrument.columns)
    instrument = instrument.rename(columns = {'price':input})
    print(instrument.head())
    return instrument[[input,'t']]

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def AddExtraFeatures(product, data, characteristics, years):
    years = list(map(str,years))
    data_with_features_ls = []
    print(data['year'].unique())
    for year in tqdm(years):
        features = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+"_with_features.tsv", delimiter = '\t')
        # y = int(year)
        year_data = data[data['year'] == year]
        # print(year_data)
        agg_dic = {}
        for characteristic in characteristics:
            agg_dic[characteristic] = 'first'
        features = features.groupby(['upc'], as_index = False).agg(agg_dic, as_index = False).reindex(columns = features.columns)
        variables = characteristics + ['upc']
        features = features[variables]
        features = features.set_index('upc')
        features_map = features.to_dict()
        for characteristic in characteristics:
            year_data[characteristic] = year_data['upc'].map(features_map[characteristic])
        data_with_features_ls.append(year_data)
    data_with_features = pd.concat(data_with_features_ls)
    return data_with_features



frequency = sys.argv[1]
product = sys.argv[2]
start = sys.argv[3]
end = sys.argv[4]
# RCLogit(product, frequency,['wheat','barley'], ['style_descr'], start, end)
SampleRCLogit(product, frequency,['wheat','barley'], ['style_descr'], start, end)
