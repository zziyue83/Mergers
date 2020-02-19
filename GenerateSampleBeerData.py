import pandas as pd
import os
from ProductModuleMap import productModuleMap
from tqdm import tqdm

# load products data and find the product entries, ex. FindProduct("BEER")
def LoadWantedProduct(product):
    products_path = "../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
    products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0)
    wantedProducts = products[(products['product_group_descr'].notnull()) & (products['product_group_descr'].str.contains(product))]
    print(wantedProducts['brand_descr'].unique().shape)
    print("Loaded "+product+" products")
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
    movementTable = pd.read_csv(movement_path, delimiter = "\t",chunksize = 100000)
    return movementTable



# beerProducts = LoadWantedProduct("BEER")
# # record beer upcs
# beer_UPCs = {}
# for index, row in beerProducts.iterrows():
#     upc = row['upc']
#     beer_UPCs[upc] = 0
#     # for purpose of running quickly
#     if len(beer_UPCs) >= 10:
#         break
# print("Finished recording beer UPCs")



#process movement files by year
years = ['2006','2007','2008','2009']
groups = [5001]
# modules = [5000,5001,5005,5010,5015,5020]
modules = [5001]
area_month_upc_Year = []
aggregation_function = {'week_end': 'first', 'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first','store_code_uc':'first'}
for year in years:
    area_month_upc_list = []
    storeTable = LoadStoreTable(year)
    storeMap = storeTable.to_dict()
    dmaMap = storeMap['dma_code']
    # for key in dmaMap:
    #     print(key)
    #     print(dmaMap[key])
    for group in groups:
        for module in modules:
            movementTable = LoadChunkedYearModuleMovementTable(year, group, module)
            print("loaded movement file of "+year+", group: "+str(group)+", module: "+str(module))
            # i = 0
            for data_chunk in tqdm(movementTable):
                # i = i+1
                data_chunk['month'] = data_chunk['week_end']/100
                data_chunk['month'] = data_chunk['month'].astype(int)
                data_chunk['fips_state_code'] = data_chunk.apply(lambda x: storeTable.loc[x['store_code_uc']].fips_state_code, axis = 1)
                data_chunk['fips_county_code'] = data_chunk.apply(lambda x: storeTable.loc[x['store_code_uc']].fips_county_code, axis = 1)
                area_month_upc = data_chunk.groupby(['month', 'upc','fips_state_code','fips_county_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
                area_month_upc_list.append(area_month_upc)
            # print(i)
            area_month_upc = pd.concat(area_month_upc_list)
            area_month_upc = area_month_upc.groupby(['month', 'upc','fips_state_code','fips_county_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_month_upc.columns)
            area_month_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)
            print(area_month_upc.shape)
            save_path = "../../GeneratedData/BEER_area_month_upc_"+str(group)+"_"+str(module)+"_"+year+".tsv"
            area_month_upc.to_csv(save_path, sep = '\t', encoding = 'utf-8')
            print("saved area-month-upc data. Year: "+year+" Group: "+str(group)+" Module: "+str(module))
            area_month_upc_Year.append(area_month_upc)

#aggregate yearly result and save as csv file
aggregation_function = {'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first'}
area_month_upc = pd.concat(area_month_upc_Year)
area_month_upc = area_month_upc.groupby(['month', 'upc','fips_state_code','fips_county_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_month_upc.columns)
area_month_upc.to_csv("../../GeneratedData/BEER_area_month_upc_5001.tsv", sep = '\t', encoding = 'utf-8')

#
#     # Example:
#     # store_code_uc      738532.0
#     # upc              15000004.0
#     # week_end         20060107.0
#     # units                   2.0
#     # prmult                  1.0
#     # price                   1.5
#     # feature                 NaN
#     # display                 NaN
#     # month              200601.0
