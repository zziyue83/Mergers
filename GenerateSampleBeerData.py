import pandas as pd
import os

# load products data and find the beer entries
products_path = "../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0)
beerProducts = products[(products['product_group_descr'].notnull()) & (products['product_group_descr'].str.contains("BEER"))]

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

#load movements data
movements_path = "../../Data/nielsen_extracts/RMS/2006/Movement_Files/5001_2006/5000_2006.tsv"
movements = pd.read_csv(movements_path, delimiter = "\t", chunksize = 1000)
upc = beerProducts.iloc[0]["upc"]

# record beer upcs
beer_UPCs = {}
for index, row in beerProducts.iterrows():
    upc = row['upc']
    beer_UPCs[upc] = 0
    # for purpose of running quickly
    if len(beer_UPCs) >= 5:
        break
print("hello")

# find data corresponding to beer upcs
# data too large so slice to chunks
chunk_list = []
for data_chunk in movements:
    filtered_chunk = data_chunk[data_chunk['upc'].isin(beer_UPCs)]
    chunk_list.append(filtered_chunk)
store_week_upc = pd.concat(chunk_list)
print(store_week_upc.shape)

# group data by month
store_week_upc['month'] = store_week_upc['week_end']/100
store_week_upc['month'] = store_week_upc['month'].astype(int)
print(store_week_upc['month'])
aggregation_function = {'week_end': 'first', 'units': 'sum', 'prmult':'sum', 'price':'mean', 'feature': 'first','display':'first'}
store_month_upc = store_week_upc.groupby(['month', 'upc','store_code_uc'], as_index = False).aggregate(aggregation_function).reindex(columns = store_week_upc.columns)
print(store_month_upc.iloc[0])
print(store_month_upc.iloc[0]['month'])
print(store_month_upc.iloc[10]['month'])
print(store_month_upc)

