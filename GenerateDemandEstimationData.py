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
    for input in inputs:
        input_prices = ReadInstrument(input)
        data = data.merge(input_prices, how = 'inner', left_on = 'y-m', right_on = 't')
        data[input] = data[input] * data['price_index']
        # print(data.head())
    data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    data['product_ids'] = data['upc'].astype(str) + data['dma_code'].astype(str)
    variables = ['dma_code_'+frequency,'adjusted_price','product_ids','market_share','distance','y-m'] + characteristics + inputs
    print(variables)
    demand_estimation_data = data[variables]
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_'+frequency:'market_ids','adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'distance':'demand_instruments0','market_share':'shares','y-m':'time'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    print(demand_estimation_data.head())
    # pyblp.options.collinear_atol = pyblp.options.collinear_rtol = 0

    #plain logit regression
    formulation = '0 + prices '
    for characteristic in characteristics:
        formulation = formulation + '+ '+ characteristic + ' '
    logit_formulation = pyblp.Formulation(formulation, absorb='C(product_ids) + C(time)')
    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)
    resultDf = pd.DataFrame.from_dict(data=logit_results.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/'+product+'_plain_logit.csv', sep = ',')

    #nested logit regression
    # demand_estimation_data['nesting_ids'] = 1
    # groups = demand_estimation_data.groupby(['market_ids', 'nesting_ids'])
    # demand_estimation_data['demand_instruments'+str(len(inputs)+1)] = groups['shares'].transform(np.size)
    # nl_formulation = pyblp.Formulation(formulation, absorb='C(product_ids) + C(time)')
    # problem = pyblp.Problem(nl_formulation, demand_estimation_data)
    # nlresults = problem.solve(rho=0.7)
    # print(nlresults)
    # resultDf = pd.DataFrame.from_dict(data=nlresults.to_dict(), orient='index')
    # resultDf.to_csv('RegressionResults/'+product+'_nested_logit.csv', sep = ',')

def TestGenerateDEData(product, frequency, inputs, characteristics, start, end):
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
    for input in inputs:
        input_prices = ReadInstrument(input)
        data = data.merge(input_prices, how = 'inner', left_on = 'y-m', right_on = 't')
        data[input] = data[input] * data['price_index']
        # print(data.head())
    data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    # data['product_ids'] = data['upc'].astype(str) + '_' + data['dma_code'].astype(str)
    variables = ['dma_code_'+frequency,'adjusted_price','market_share','distance','y-m','upc','dma_code'] + characteristics + inputs
    # variables = ['dma_code_'+frequency,'adjusted_price','market_share','distance','y-m','product_ids'] + characteristics + inputs
    print(variables)
    demand_estimation_data = data[variables]
    print(demand_estimation_data.head())
    rename_dic = {'dma_code_'+frequency:'market_ids','adjusted_price':'prices','upc':'product_ids','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'distance':'demand_instruments0','market_share':'shares','y-m':'time','dma_code':'city_ids'}
    # rename_dic = {'dma_code_'+frequency:'market_ids','adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'distance':'demand_instruments0','market_share':'shares','y-m':'time'}
    for i in range(len(inputs)):
        rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    print(demand_estimation_data.head())
    # pyblp.options.collinear_atol = pyblp.options.collinear_rtol = 0

    #plain logit regression
    formulation = '0 + prices '
    for characteristic in characteristics:
        formulation = formulation + '+ '+ characteristic + ' '
    logit_formulation = pyblp.Formulation(formulation, absorb='C(product_ids)*C(city_ids) + C(time)')
    problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    print(problem)
    logit_results = problem.solve()
    print(logit_results)
    resultDf = pd.DataFrame.from_dict(data=logit_results.to_dict(), orient='index')
    resultDf.to_csv('RegressionResults/test_'+product+'_plain_logit.csv', sep = ',')

    #nested logit regression
    # demand_estimation_data['nesting_ids'] = 1
    # groups = demand_estimation_data.groupby(['market_ids', 'nesting_ids'])
    # demand_estimation_data['demand_instruments'+str(len(inputs)+1)] = groups['shares'].transform(np.size)
    # nl_formulation = pyblp.Formulation(formulation, absorb='C(product_ids) + C(time)')
    # problem = pyblp.Problem(nl_formulation, demand_estimation_data)
    # nlresults = problem.solve(rho=0.7)
    # print(nlresults)
    # resultDf = pd.DataFrame.from_dict(data=nlresults.to_dict(), orient='index')
    # resultDf.to_csv('RegressionResults/'+product+'_nested_logit.csv', sep = ',')

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

# def AdjustInflation(frequency):
#     cpiu = pd.read_excel('cpiu_2000_2020.xlsx', header = 11)
#     cpiu = cpiu.set_index('Year')
#     month_dictionary = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
#     cpiu = cpiu.rename(columns = month_dictionary)
#     cpiu = cpiu.drop(['HALF1','HALF2'], axis=1)
#     cpiu = cpiu.stack()
#     # cpiu_202001 = float(cpiu.loc[(2020,1)])
#     cpiu = cpiu.reset_index().rename(columns = {'level_1':'month',0:'cpiu'})
#     if frequency == 'quarter':
#         cpiu['quarter'] = cpiu['month'].apply(lambda x: 1 if x <=3 else 2 if ((x>3) & (x<=6)) else 3 if ((x>6) & (x<=9)) else 4)
#         cpiu = cpiu.groupby(['Year', frequency]).agg({'cpiu': 'mean'})
#     if frequency == 'month':
#         cpiu = cpiu.set_index(['Year', frequency])
#     cpiu_202001 = float(cpiu.loc[(2020,1)])
#     cpiu['price_index'] = cpiu_202001/cpiu['cpiu']
#     cpiu = cpiu.reset_index()
#     cpiu['t'] = cpiu['Year'] * 100 + cpiu[frequency]
#     cpiu = cpiu.set_index('t')
#     return cpiu



frequency = sys.argv[1]
product = sys.argv[2]
start = sys.argv[3]
end = sys.argv[4]
# input = 'barley'
# instrument = ReadInstrument(input)
# print(instrument['t'])
# GenerateDEData(product, frequency,['wheat','barley'], ['style_descr'], start, end)
TestGenerateDEData(product, frequency,['wheat','barley'], ['style_descr'], start, end)
