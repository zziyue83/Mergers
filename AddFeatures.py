import pandas as pd
import sys
import numpy as np

def AddExtraFeatures(products):
    years = [2006, 2007, 2008, 2009]
    years = list(map(str,years))
    add_features = pd.DataFrame()
    for product in products:
        for year in years:
            features_year = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+"_with_features.tsv", delimiter = '\t', index_col = 1)
            features_year['year'] = year
            features_year['product'] = product
            features_year['upc_year'] = features_year['upc'].astype(str) + ' ' + features_year['year'].astype(str)
            if (product == 'CANDY') or (product == 'GUM'):
                features_year['mint'] = np.where(features_year['flavor_descr'].str.contains('MINT'), 'NON-MINT', 'MINT')
                print(features_year.iloc[0])
            if add_features.empty:
                add_features = features_year
            else:
                add_features = pd.concat([add_features, features_year])
    return add_features


def GenerateDEData(products, quarterOrMonth, inputs, characteristics):
    data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_model" + "_with_distance.tsv", delimiter = '\t')
    for input in inputs:
        input_prices = ReadInstrument(input, quarterOrMonth)
        data[input] = data[quarterOrMonth].map(input_prices.set_index(quarterOrMonth)[input])
        print(data.head())
    add_features = AddExtraFeatures(products)
    data['upc_year'] = data['upc'].astype(str) + ' ' + data['year'].astype(str)
    print(add_features.iloc[0])
    for characteristic in characteristics:
        data[characteristic] = data['upc_year'].map(add_features.drop_duplicates().set_index('upc_year')[characteristic])
    print(data.iloc[0])
    data['dma_code_' + quarterOrMonth] = data['dma_code'].astype(str) + data[quarterOrMonth].astype(str)
    variables = ['dma_code_' + quarterOrMonth,'log_adjusted_price','upc','market_share','distance']
    for input in inputs:
        variables.append(input)
    for characteristic in characteristics:
        variables.append(characteristic)
    print(variables)
    demand_estimation_data = data[variables]
    demand_estimation_data = demand_estimation_data.dropna()
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_'+quarterOrMonth:'market_ids','log_adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',quarterOrMonth+'_since_start':quarterOrMonth,'upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    j = -1
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(j+1)
    for i in range(len(characteristics)):
        rename_dic[characteristics[i]] = 'demand_instruments'+str(j+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    print(demand_estimation_data.iloc[0])
    print(demand_estimation_data.head())
    # pyblp.options.collinear_atol = pyblp.options.collinear_rtol = 0
    logit_formulation = pyblp.Formulation('prices')
    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)

def ReadInstrument(input, quarterOrMonth, skiprows = 0):
    instrument = pd.read_csv(input+'.csv', skiprows = skiprows, delimiter = ',')
    if quarterOrMonth == 'month':
        instrument[quarterOrMonth] = pd.to_datetime(instrument['t']).dt.to_period('M').astype(str)
    if quarterOrMonth == 'quarter':
        instrument[quarterOrMonth] = pd.to_datetime(instrument['t']).dt.to_period('Q').astype(str)
    else:
        print('error')
    instrument = instrument.groupby(quarterOrMonth, as_index = False).agg({'Price':'mean','t':'first'},as_index = False).reindex(columns = instrument.columns)
    instrument = instrument.rename(columns = {'Price':input})
    print(instrument.head())
    return instrument[[input,quarterOrMonth]]

quarterOrMonth = sys.argv[1]
#products = [sys.argv[2]]
#inputs = [sys.argv[3]]
#characteristics = [sys.argv[4]]
products = [sys.argv[2], sys.argv[3]]
inputs = [sys.argv[4], sys.argv[5]]
characteristics = [sys.argv[6], sys.argv[7]]
GenerateDEData(products, quarterOrMonth, inputs, characteristics)
