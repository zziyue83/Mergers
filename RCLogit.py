import pandas as pd
import sys
import pyblp
import numpy as np
from tqdm import tqdm

def RCLogit(product, frequency, inputs, characteristics, start, end):
    data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
    data['y-m'] = pd.to_datetime(data['y-m-d']).dt.to_period('M')
    data['year'] = pd.to_datetime(data['y-m-d']).dt.to_period('Y')
    data['year'] = data['year'].astype(str)
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
    variables = ['dma_code_'+frequency,'adjusted_price','market_share','y-m','upc','dma_code','owner initial','brand_descr'] + characteristics + inputs
    # variables = ['dma_code_'+frequency,'adjusted_price','market_share','distance','y-m','product_ids'] + characteristics + inputs
    print(variables)
    demand_estimation_data = data[variables]
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_'+frequency:'market_ids','adjusted_price':'prices','upc':'product_ids','owner initial':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'distance':'demand_instruments0','market_share':'shares','y-m':'time','dma_code':'city_ids'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    print(demand_estimation_data.head())

    #random coeffcient logit regression
    x2formulation = '1 + prices'
    for characteristic in characteristics:
        x2formulation = ' ' + x2formulation + '+ '+ characteristic

    X1_formulation = pyblp.Formulation('0 + prices', absorb='C(product_ids)+C(time)')
    X2_formulation = pyblp.Formulation(x2formulation)
    product_formulations = (X1_formulation, X2_formulation)

    mc_integration = pyblp.Integration('monte_carlo', size=50, specification_options={'seed': 0})

    pr_integration = pyblp.Integration('product', size=5)

    mc_problem = pyblp.Problem(product_formulations, product_data, integration=mc_integration)
    print(mc_problem)
    pr_problem = pyblp.Problem(product_formulations, product_data, integration=pr_integration)
    print(pr_problem)

    bfgs = pyblp.Optimization('bfgs', {'gtol': 1e-10})

    # here 3 should be replaced by K2, which is printed above in mc_problem as linear demand estimators. For beer K2 is 3. using the identity matrix as covariance matrix
    results1 = mc_problem.solve(sigma=np.eye(3), optimization=bfgs)
    print(results1)
    resultDf = pd.DataFrame.from_dict(data=results1.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/test_'+product+'_rc_logit_monte_carlo.csv', sep = ',')

    results2 = pr_problem.solve(sigma=np.eye(3), optimization=bfgs)
    print(results2)
    resultDf = pd.DataFrame.from_dict(data=results2.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/test_'+product+'_rc_logit_product_rules.csv', sep = ',')

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
RCLogit(product, frequency,['wheat','barley'], ['style_descr'], start, end)
