import pandas as pd
import sys
import pyblp
import numpy as np

def GenerateDEData(product, frequency, inputs):
    data = pd.read_csv("../../GeneratedData/" + product + "_pre_model_" + frequency + "_with_distance.tsv", delimiter = '\t')
    # print(data['y-m-d'])
    # for input in inputs:
    #     input_prices = ReadInstrument(input)
    #     data['y-m'] = pd.to_datetime(data['y-m-d']).dt.to_period('M')
    #     data = data.merge(input_prices, how = 'inner', left_on = 'y-m', right_on = 't')
    #     print(data.head())
    # data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    # x = data['distance']
    data['constant'] = 1
    data = data.dropna()
    x = data[['distance','constant']].to_numpy()

    z = np.transpose(x)
    y = np.matmul(z, x)
    print(x)
    u = np.linalg.inv(y)
    print(u)
    # variables = ['dma_code_'+frequency,'log_adjusted_price','upc','market_share']
    # for input in inputs:
    #     variables.append(input)
    # print(variables)
    # demand_estimation_data = data[variables]
    # print(demand_estimation_data.head())
    # rename_dic = {'dma_code_'+frequency:'market_ids','log_adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    # for i in range(len(inputs)):
    #     rename_dic[inputs[i]] = 'demand_instruments'+str(i)
    # demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    # print(demand_estimation_data.head())
    # pyblp.options.collinear_atol = pyblp.options.collinear_rtol = 0
    # logit_formulation = pyblp.Formulation('prices')
    # problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    # print(problem)
    # logit_results = problem.solve()
    # print(logit_results)

def ReadInstrument(input, skiprows = 0):
    instrument = pd.read_csv(input+'.csv', skiprows = skiprows, delimiter = ',')
    instrument['t'] = pd.to_datetime(instrument['date']).dt.to_period('M')
    instrument = instrument.groupby('t',as_index = False).agg({'value':'mean','date':'first'},as_index = False).reindex(columns = instrument.columns)
    instrument = instrument.rename(columns = {'value':input})
    print(instrument.head())
    return instrument[[input,'t']]



frequency = sys.argv[1]
product = sys.argv[2]
# input = 'barley'
# instrument = ReadInstrument(input)
# print(instrument['t'])
GenerateDEData(product, frequency, inputs = ['wheat'])
