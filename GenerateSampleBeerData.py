import pandas as pd
import os
from ProductModuleMap import productModuleMap

# load products data and find the beer entries
products_path = "../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0)
beerProducts = products[(products['product_group_descr'].notnull()) & (products['product_group_descr'].str.contains("BEER"))]

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

# record beer upcs
beer_UPCs = {}
for index, row in beerProducts.iterrows():
    upc = row['upc']
    beer_UPCs[upc] = 0
    # for purpose of running quickly
    if len(beer_UPCs) >= 10:
        break
print("Finished recording beer UPCs")

#process movement files by year
years = ['2006','2007','2008','2009']
store_month_upc_Year = []
for year in years:
    #load movements data
    # movements_path = "../../Data/nielsen_extracts/RMS/2006/Movement_Files/5001_2006/5000_2006.tsv"
    movements_path = "../../Data/nielsen_extracts/RMS/"+year+"/Movement_Files/5001_"+year+"/5000_"+year+".tsv"
    movements = pd.read_csv(movements_path, delimiter = "\t", chunksize = 1000)

    # find data corresponding to beer upcs
    # data too large so slice to chunks
    chunk_list = []
    for data_chunk in movements:
        filtered_chunk = data_chunk[data_chunk['upc'].isin(beer_UPCs)]
        chunk_list.append(filtered_chunk)
    store_week_upc = pd.concat(chunk_list)
    print(store_week_upc.shape)

    # group data by month, upc, store_code_uc
    store_week_upc['month'] = store_week_upc['week_end']/100
    store_week_upc['month'] = store_week_upc['month'].astype(int)
    aggregation_function = {'week_end': 'first', 'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first'}
    store_month_upc = store_week_upc.groupby(['month', 'upc','store_code_uc'], as_index = False).aggregate(aggregation_function).reindex(columns = store_week_upc.columns)
    store_month_upc_Year.append(store_month_upc)
    print(store_month_upc)

#aggregate yearly result and save as csv file
store_month_upc = pd.concat(store_month_upc_Year)
store_month_upc.drop('week_end', axis=1, inplace=True)
store_month_upc.to_csv("../../GeneratedData/BEER_store_month_upc.tsv", sep = '\t', encoding = 'utf-8')

    # Example:
    # store_code_uc      738532.0
    # upc              15000004.0
    # week_end         20060107.0
    # units                   2.0
    # prmult                  1.0
    # price                   1.5
    # feature                 NaN
    # display                 NaN
    # month              200601.0
