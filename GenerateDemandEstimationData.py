import pandas as pd
import sys
import pyblp
import numpy as np
from tqdm import tqdm

def GenerateDEData(product, frequency, inputs, characteristics, start, end):
    data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
    # print(data['y-m-d'])
    data['y-m'] = pd.to_datetime(data['y-m-d']).dt.to_period('M')
    data['year'] = pd.to_datetime(data['y-m-d']).dt.to_period('Y')
    data['year'] = data['year'].astype(str)
    # print(data[['upc','year']])
    years = GenerateYearList(start, end)
    data = AddExtraFeatures(product, data, characteristics, years)
    data = data.dropna()
    print(data.shape)
    print(data.columns)
    # print(data['style_descr'].value_counts())
    # print(pd.isna(data['style_descr']).value_counts())
    for characteristic in characteristics:
        if characteristic == 'style_descr':
            data['style_descr'] = np.where(data['style_descr'] == 'DOMESTIC', 0, 1)
    print(data['style_descr'].value_counts())
    for input in inputs:
        input_prices = ReadInstrument(input)
        data = data.merge(input_prices, how = 'inner', left_on = 'y-m', right_on = 't')
        # print(data.head())
    data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    # x = data['distance']
    # data['constant'] = 1
    # data = data.dropna()
    # x = data[['distance','constant']].to_numpy()
    #
    # z = np.transpose(x)
    # y = np.matmul(z, x)
    # print(x)
    # u = np.linalg.inv(y)
    # print(u)
    variables = ['dma_code_'+frequency,'adjusted_price','upc','market_share','distance','y-m'] + characteristics + inputs
    print(variables)
    demand_estimation_data = data[variables]
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_'+frequency:'market_ids','adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'upc':'product_ids','distance':'demand_instruments0','market_share':'shares','y-m':'time'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    print(demand_estimation_data.head())
    # pyblp.options.collinear_atol = pyblp.options.collinear_rtol = 0
    logit_formulation = pyblp.Formulation('prices', absorb='C(product_ids) + C(time)')
    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)
    resultDf = pd.from_dict(data=logit_results.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/'+product+'_plain_logit.csv', dep = ',')

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
        # print(features)
        # print(features_map['style_descr'])
        # print(year_data['upc'])
        # data = data.merge(features, how = 'left', left_on = ['upc','year'], right_on = ['upc','panel_year'])
        for characteristic in characteristics:
            year_data[characteristic] = year_data['upc'].map(features_map[characteristic])
        # print('wuhu')
        # print(year_data['style_descr'])
        data_with_features_ls.append(year_data)
        # print('wuhuwuhu')
    data_with_features = pd.concat(data_with_features_ls)
    return data_with_features



frequency = sys.argv[1]
product = sys.argv[2]
start = sys.argv[3]
end = sys.argv[4]
# input = 'barley'
# instrument = ReadInstrument(input)
# print(instrument['t'])
GenerateDEData(product, frequency,['wheat','barley'], ['style_descr'], start, end)
