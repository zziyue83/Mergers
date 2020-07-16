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
                features_year['mint'] = np.where((features_year['flavor_descr'].str.contains('MINT')) & (features_year['flavor_descr'].notna()), 1, 0)
                features_year['chocolate'] = np.where((features_year['variety_descr']=='CHOCOLATE') & (features_year['variety_descr'].notna()), 1, 0)
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
        data[input] = data[quarterOrMonth].map(input_prices[input])
        data[input] = data[input]*data['price_index']
        print(data.head())
    add_features = AddExtraFeatures(products)
    data['upc_year'] = data['upc'].astype(str) + ' ' + data['year'].astype(str)
    for characteristic in characteristics:
        data[characteristic] = data['upc_year'].map(add_features.drop_duplicates('upc_year').set_index('upc_year')[characteristic])
    print(data.iloc[0])
    if len(products) > 1:
        for product in products:
            data[product] = np.where(data['product'] == product, 1, 0)
    print(data.iloc[0])
    data['dma_code_' + quarterOrMonth] = data['dma_code'].astype(str) + ' ' + data[quarterOrMonth].astype(str)
    data.to_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + "_pre_estimation.tsv", sep = '\t', encoding = 'utf-8')

def ReadInstrument(input, quarterOrMonth, skiprows = 0):
    instrument = pd.read_csv(input+'.csv', skiprows = skiprows, delimiter = ',')
    if quarterOrMonth == 'month':
        instrument[quarterOrMonth] = pd.to_datetime(instrument['t']).dt.strftime("%Y%m").astype(int)
    if quarterOrMonth == 'quarter':
        instrument[quarterOrMonth] = pd.to_datetime(instrument['t']).dt.to_period('Q').astype(str)
    else:
        print('error')
    instrument = instrument.groupby(quarterOrMonth).agg({'Price':'mean'})
    instrument = instrument.rename(columns = {'Price':input})
    print(instrument.head())
    return instrument[[input]]

quarterOrMonth = sys.argv[1]
#products = [sys.argv[2]]
#inputs = [sys.argv[3]]
#characteristics = [sys.argv[4]]
products = [sys.argv[2], sys.argv[3]]
inputs = [sys.argv[4], sys.argv[5]]
characteristics = [sys.argv[6], sys.argv[7]]
GenerateDEData(products, quarterOrMonth, inputs, characteristics)
