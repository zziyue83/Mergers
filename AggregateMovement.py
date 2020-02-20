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
    group = int(product_group_code)
    wantedProducts = products[products['product_group_code'] == group]
    product = wantedProducts.iloc[0]['product_group_descr']
    print("Loaded "+product+" products, group code: " + str(product_group_code))
    return product, wantedProducts

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

def LoadChunkedYearModuleMovementTable(year = 2006, group = 5001, module = 5000, path = ''):
    if path == '':
        movement_path = "../../Data/nielsen_extracts/RMS/"+str(year)+"/Movement_Files/"+group+"_"+str(year)+"/"+str(module)+"_"+str(year)+".tsv"
        movementTable = pd.read_csv(movement_path, delimiter = "\t", chunksize = 10000000)
    else:
        movementTable = pd.read_csv(path, delimiter = "\t", chunksize = 10000000)
    return movementTable

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    years = []
    for i in range(s, e+1):
        years.append(str(i))
    return years

def AggregateMovement(years, groups):
    aggregation_function = {'week_end': 'first', 'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first','store_code_uc':'first','sales':'sum'}
    group = groups[0]
    product, products = LoadWantedProduct(group)
    productMap = products.to_dict()
    for year in years:
        area_month_upc_Year = []
        storeTable = LoadStoreTable(year)
        storeMap = storeTable.to_dict()
        dmaMap = storeMap['dma_code']

        for group in groups:
            countDownMerge = 5
            rootdir = "/projects/b1048/gillanes/Mergers/Data/nielsen_extracts/RMS/"+year+"/Movement_Files/"+group+"_"+year
            for file in os.listdir(rootdir):
                if "tsv" in file and year in file:
                    path = os.path.join(rootdir, file)
                    area_month_upc_list = []
                    movementTable = LoadChunkedYearModuleMovementTable(path = path)
                    print("loaded movement file of " + file)
                    # i = 0
                    # for data_chunk in tqdm(movementTable):
                    #     i += 1
                    # print("total chunks: "+str(i))
                    # movementTable = LoadChunkedYearModuleMovementTable(path = path)
                    for data_chunk in tqdm(movementTable):
                        data_chunk['month'] = data_chunk['week_end']/100
                        data_chunk['month'] = data_chunk['month'].astype(int)
                        data_chunk['dma_code'] = data_chunk['store_code_uc'].map(dmaMap)
                        data_chunk['sales'] = data_chunk['price'] * data_chunk['units'] / data_chunk['prmult']
                        # data_chunk['fips_state_code'] = data_chunk.apply(lambda x: storeTable.loc[x['store_code_uc']].fips_state_code, axis = 1)
                        # data_chunk['fips_county_code'] = data_chunk.apply(lambda x: storeTable.loc[x['store_code_uc']].fips_county_code, axis = 1)
                        area_month_upc = data_chunk.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
                        area_month_upc_list.append(area_month_upc)
                    area_month_upc = pd.concat(area_month_upc_list)
                    area_month_upc = area_month_upc.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_month_upc.columns)
                    print(area_month_upc.shape)
                    area_month_upc_Year.append(area_month_upc)
                    countDownMerge -= 1
                    if countDownMerge == 0:
                        area_month_upc = pd.concat(area_month_upc_Year)
                        area_month_upc_Year = []
                        area_month_upc_Year.append(area_month_upc)
                        countDownMerge = 5

        area_month_upc = pd.concat(area_month_upc_Year)
        area_month_upc = area_month_upc.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_month_upc.columns)
        area_month_upc['brand_code_uc'] = area_month_upc['upc'].map(productMap['brand_code_uc'])
        area_month_upc['brand_descr'] = area_month_upc['upc'].map(productMap['brand_descr'])
        area_month_upc['multi'] = area_month_upc['upc'].map(productMap['multi'])
        area_month_upc['size1_amount'] = area_month_upc['upc'].map(productMap['size1_amount'])
        area_month_upc['volume'] = area_month_upc['units'] * area_month_upc['size1_amount'] * area_month_upc['multi']
        area_month_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)
        area_month_upc.to_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv", sep = '\t', encoding = 'utf-8')
        print("Saved dma_month_upc data for year "+year)


if len(sys.argv) < 3:
    print("Not enough arguments")
    sys.exit()

group = sys.argv[1]
start = sys.argv[2]
end = sys.argv[3]
years = GenerateYearList(start, end)
print(years)
groups = [group]
AggregateMovement(years, groups)
