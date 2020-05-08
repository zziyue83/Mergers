import pandas as pd
import sys
import pyblp
import numpy as np

def GenerateDEData(product, frequency, inputs):
    data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
    print(data['y-m-d'])
    data['y-m'] = pd.to_datetime(data['y-m-d']).dt.to_period('M')
    data['year'] = pd.to_datetime(data['y-m-d']).dt.to_period('Y')
    print(data[['upc','year']])
    # for input in inputs:
    #     input_prices = ReadInstrument(input)
    #     data = data.merge(input_prices, how = 'inner', left_on = 'y-m', right_on = 't')
    #     print(data.head())
    # data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    # # x = data['distance']
    # # data['constant'] = 1
    # # data = data.dropna()
    # # x = data[['distance','constant']].to_numpy()
    # #
    # # z = np.transpose(x)
    # # y = np.matmul(z, x)
    # # print(x)
    # # u = np.linalg.inv(y)
    # # print(u)
    # variables = ['dma_code_'+frequency,'log_adjusted_price','upc','market_share','distance']
    # for input in inputs:
    #     variables.append(input)
    # print(variables)
    # demand_estimation_data = data[variables]
    # # demand_estimation_data = demand_estimation_data.dropna()
    # print(demand_estimation_data.head())
    # rename_dic = {'dma_code_'+frequency:'market_ids','log_adjusted_price':'prices','Firm':'firm_ids','brand_descr':'brand_ids',frequency+'_since_start':frequency,'upc':'product_ids','distance':'demand_instruments0','market_share':'shares'}
    # for i in range(len(inputs)):
    #     rename_dic[inputs[i]] = 'demand_instruments'+str(i+1)
    # demand_estimation_data = demand_estimation_data.rename(columns = rename_dic)
    # print(demand_estimation_data.head())
    # # pyblp.options.collinear_atol = pyblp.options.collinear_rtol = 0
    # logit_formulation = pyblp.Formulation('prices')
    # problem = pyblp.Problem(logit_formulation, demand_estimation_data)
    # print(problem)
    # logit_results = problem.solve()
    # print(logit_results)

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

def AddExtraFeatures(product, years):
    years = list(map(str,years))
    brandsCumuYear = []
    for year in years:
        firstFile = True
        savePath = "../../GeneratedData/"+product+"_dma_month_upc_"+year+"_with_features.tsv"
        movement = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv", delimiter = '\t' , index_col = "upc" , chunksize = 1000000)
        features = pd.read_csv("../../Data/nielsen_extracts/RMS/"+year+"/Annual_Files/products_extra_"+year+".tsv", delimiter = '\t', index_col = 'upc')
        for data_chunk in tqdm(movement):
            merged = data_chunk.merge(features, how = 'left', left_index = True, right_index = True)
            if firstFile:
                merged.to_csv(savePath, sep = '\t')
                firstFile = False
            else:
                merged.to_csv(savePath, sep = '\t', header = False, mode = 'a')



frequency = sys.argv[1]
product = sys.argv[2]
start = sys.argv[3]
end = sys.argv[4]
# input = 'barley'
# instrument = ReadInstrument(input)
# print(instrument['t'])
GenerateDEData(product, frequency, inputs = ['wheat','barley'], start, end)
