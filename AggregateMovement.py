#!/usr/bin/python

import sys
import os
import pandas as pd
from ProductModuleMap import productModuleMap
from tqdm import tqdm

# load products data and find the product entries, ex. FindProduct("BEER")
def LoadWantedProduct(product_group_code):
    products_path = "../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
    products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = "upc")
    wantedProducts = products[products['product_group_code'] == product_group_code]
    product = wantedProducts.iloc[0]['product_group_descr']
    print("Loaded "+product+" products, group code: " + str(product_group_code))
    return wantedProducts

#Example:
# upc                                   15000004
# upc_ver_uc                                   1
# upc_descr               SIERRA NEVADA W BR NRB
# product_module_code                       5000
# product_module_descr                      BEER
# product_group_code                        5001
# product_group_descr                       BEER
# department_code                              8
# department_descr           ALCOHOLIC BEVERAGES
# brand_code_uc                           637860
# brand_descr                SIERRA NEVADA WHEAT
# multi                                        1
# size1_code_uc                            32992
# size1_amount                                12
# size1_units                                 OZ
# dataset_found_uc                           ALL
# size1_change_flag_uc                         0

def LoadStoreTable(year):
    store_path = "../../Data/nielsen_extracts/RMS/"+year+"/Annual_Files/stores_"+year+".tsv"
    storeTable = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
    print("Loaded store file of "+ year)
    return storeTable

def LoadChunkedYearModuleMovementTable(year, group, module):
    movement_path = "../../Data/nielsen_extracts/RMS/"+str(year)+"/Movement_Files/"+str(group)+"_"+str(year)+"/"+str(module)+"_"+str(year)+".tsv"
    movementTable = pd.read_csv(movement_path, delimiter = "\t",chunksize = 1000000)
    return movementTable

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    years = []
    for i in range(s, e+1):
        years.append(str(i))
    return years

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
if len(sys.argv) < 3:
    print("Not enough arguments")
    sys.exit()

group = sys.argv[1]
group = int(group)
print(group)

start = sys.argv[2]
end = sys.argv[3]
years = GenerateYearList(start, end)
print(years)


for year in years:
    rootdir = "/projects/b1048/gillanes/Mergers/Data/nielsen_extracts/RMS/"+year+"/Movement_Files/"+group+"_"+year
    for file in os.listdir(rootdir):
        if "tsv" in file:
            path = os.path.join(rootdir, file)
            print(path)

# #process movement files by year
# years = ['2006','2007','2008','2009']
# groups = [5001]
# modules = [5000,5001,5005,5010,5015,5020]
# aggregation_function = {'week_end': 'first', 'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first','store_code_uc':'first','sales':'sum'}
# products = LoadWantedProduct(5001)
# productMap = products.to_dict()
# for year in years:
#     area_month_upc_Year = []
#     storeTable = LoadStoreTable(year)
#     storeMap = storeTable.to_dict()
#     dmaMap = storeMap['dma_code']
#
#     for group in groups:
#         for module in modules:
#             area_month_upc_list = []
#             movementTable = LoadChunkedYearModuleMovementTable(year, group, module)
#             print("loaded movement file of "+year+", group: "+str(group)+", module: "+str(module))
#             for data_chunk in tqdm(movementTable):
#                 data_chunk['month'] = data_chunk['week_end']/100
#                 data_chunk['month'] = data_chunk['month'].astype(int)
#                 data_chunk['dma_code'] = data_chunk['store_code_uc'].map(dmaMap)
#                 data_chunk['sales'] = data_chunk['price'] * data_chunk['units'] / data_chunk['prmult']
#                 # data_chunk['fips_state_code'] = data_chunk.apply(lambda x: storeTable.loc[x['store_code_uc']].fips_state_code, axis = 1)
#                 # data_chunk['fips_county_code'] = data_chunk.apply(lambda x: storeTable.loc[x['store_code_uc']].fips_county_code, axis = 1)
#                 # data_chunk['size1_amount'] = data_chunk['upc'].map(productMap['size1_amount'])
#                 # data_chunk['multi'] = data_chunk['upc'].map(productMap['multi'])
#                 # data_chunk['brand_code_uc'] = data_chunk['upc'].map(productMap['brand_code_uc'])
#                 # data_chunk['brand_descr'] = data_chunk['upc'].map(productMap['brand_descr'])
#                 area_month_upc = data_chunk.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
#                 area_month_upc_list.append(area_month_upc)
#             area_month_upc = pd.concat(area_month_upc_list)
#             area_month_upc = area_month_upc.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_month_upc.columns)
#             print(area_month_upc.shape)
#             area_month_upc_Year.append(area_month_upc)
#
#     area_month_upc = pd.concat(area_month_upc_Year)
#     area_month_upc = area_month_upc.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_month_upc.columns)
#     area_month_upc['brand_code_uc'] = area_month_upc['upc'].map(productMap['brand_code_uc'])
#     area_month_upc['brand_descr'] = area_month_upc['upc'].map(productMap['brand_descr'])
#     area_month_upc['multi'] = area_month_upc['upc'].map(productMap['multi'])
#     area_month_upc['size1_amount'] = area_month_upc['upc'].map(productMap['size1_amount'])
#     area_month_upc['volume'] = area_month_upc['units'] * area_month_upc['size1_amount'] * area_month_upc['multi']
#     area_month_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)
#     area_month_upc.to_csv("../../GeneratedData/BEER_dma_month_upc_"+year+".tsv", sep = '\t', encoding = 'utf-8')
#     print("Saved dma_month_upc data for year "+year)
