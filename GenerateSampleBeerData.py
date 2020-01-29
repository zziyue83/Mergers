import pandas as pd
import os

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

movements_path = "../../Data/nielsen_extracts/RMS/2006/Movement_Files/5001_2006/5000_2006.tsv"
movements = pd.read_csv(movements_path, delimiter = "\t", chunksize = 10000)
chunk = movements.get_chunk(1)
print(chunk.iloc[0])
upc = beerProducts.iloc[0]["upc"]
weekend = beerProducts.iloc[0]["upc"]
print(upc)
print(weekend)

chunk_list = []
for data_chunk in movements:
    filtered_chunk = data_chunk[data_chunk["upc"] == upc]
    chunk_list.append(filtered_chunk)

upc_movements = pd.concat(chunk_list)
print(upc_movements.iloc[0])
