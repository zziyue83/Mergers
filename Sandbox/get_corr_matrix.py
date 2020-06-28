import re
import sys
from datetime import datetime
import unicodecsv as csv
import auxiliary as aux
from tqdm import tqdm
import os
import pandas as pd
import numpy as np

def get_corr_matrix(code, years, groups, modules, merger_date, pre_months = 24, post_months = 24, brandnumber = 10, test_brand_code = '568830'):

    dt = datetime.strptime(merger_date, '%Y-%m-%d')
    month_int = dt.year * 12 + dt.month
    min_year, min_month = aux.int_to_month(month_int - pre_months)
    max_year, max_month = aux.int_to_month(month_int + post_months)

    brand_data_list = []
    product_map = aux.get_product_map(list(set(groups)))
    
    for group, module in zip(groups, modules):
        for year in years:
            movement_table = aux.load_chunked_year_module_movement_table(year, group, module)
            upc_ver_map = aux.get_upc_ver_uc_map(year)
            
            for data_chunk in tqdm(movement_table):
                if int(year) == min_year or int(year) == max_year:
                    data_chunk['month'] = np.floor((data_chunk['week_end'] % 10000)/100).astype(int)
                    if int(year) == min_year:
                        data_chunk = data_chunk[data_chunk.month >= min_month]
                    else:
                        data_chunk = data_chunk[data_chunk.month <= max_month]
                data_chunk['store-week'] = data_chunk['store_code_uc'].astype(str) + ' ' + data_chunk['week_end'].astype(str)
                data_chunk['upc_ver_uc'] = data_chunk['upc'].map(upc_ver_map)
                data_chunk = data_chunk.join(product_map[['brand_code_uc']], on=['upc','upc_ver_uc'], how='left')
                brand_data_chunk = data_chunk[data_chunk['brand_code_uc'] == int(test_brand_code)]
                brand_data_chunk = brand_data_chunk[['upc','store-week','price']].drop_duplicates()
                brand_data_list.append(brand_data_chunk)
        
    brand_data = pd.concat(brand_data_list).drop_duplicates()
    brand_data = brand_data.pivot_table(index = 'store-week', columns = 'upc', values = 'price', aggfunc = 'first')
    print(brand_data)
    corr = brand_data.corr()
    print(corr)
    corr.to_csv('../../../All/m_' + code + '/intermediate/' + test_brand_code + '_corr.csv', sep = ',')

    # more generalized code
    '''brands = pd.read_csv('../../../All/m_' + code + '/intermediate/brands.csv')
    test_brands = brands.head(brandnumber)
    for brand in test_brands['brand']:
        for group, module in zip(groups, modules):
            for year in years:
                movement_table = aux.load_chunked_year_module_movement_table(year, group, module)
                upc_ver_map = aux.get_upc_ver_uc_map(year)
                
                for data_chunk in tqdm(movement_table):
                    if int(year) == min_year or int(year) == max_year:
                        data_chunk['month'] = np.floor((data_chunk['week_end'] % 10000)/100).astype(int)
                        if int(year) == min_year:
                            data_chunk = data_chunk[data_chunk.month >= min_month]
                        else:
                            data_chunk = data_chunk[data_chunk.month <= max_month]
                    data_chunk['store-week'] = data_chunk['store_code_uc'].astype(str) + ' ' + data_chunk['week_end'].astype(str)
                    data_chunk['upc_ver_uc'] = data_chunk['upc'].map(upc_ver_map)
                    data_chunk = data_chunk.join(product_map[['brand_descr']], on=['upc','upc_ver_uc'], how='left')
                    brand_data_chunk = data_chunk[data_chunk['brand_descr'] == brand]
                    brand_data_chunk = brand_data_chunk[['upc','store-week','price']].drop_duplicates()
                    brand_data_list.append(brand_data_chunk)
            
        brand_data = pd.concat(brand_data_list)
        brand_data = brand_data.drop_duplicates()
        brand_data = brand_data.pivot(index = 'store-week', columns = 'upc', values = 'price')
        print(brand_data)
        corr = brand_data.corr()
        print(corr)
        corr.to_csv('../../../All/m_' + code + '/intermediate/' + brand + '_corr.csv', sep = ',')'''

code = sys.argv[1]
if not os.path.isdir('../../../All/m_' + code + '/output'):
	os.makedirs('../../../All/m_' + code + '/output')
log_out = open('../../../All/m_' + code + '/output/get_corr_matrix.log', 'w')
log_err = open('../../../All/m_' + code + '/output/get_corr_matrix.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = aux.parse_info(code)

merger_date = info_dict['DateCompleted']
groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

get_corr_matrix(code, years, groups, modules, merger_date)

log_out.close()
log_err.close()