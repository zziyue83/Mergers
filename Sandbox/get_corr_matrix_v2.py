import re
import sys
from datetime import datetime
import unicodecsv as csv
import auxiliary as aux
from tqdm import tqdm
import os
import pandas as pd
import numpy as np
import timeit

def vcorrcoef(df):
    df = df.fillna(0)
    x_mean = np.mean(df,axis=0)
    r_num = np.transpose(df-x_mean).dot(df-x_mean)
    r_den = pd.DataFrame()
    for col in df.columns:
        r_den_col = pd.DataFrame(np.sqrt(np.sum((df-x_mean)**2,axis=0)*np.sum((df[col]-np.mean(df[col]))**2))).rename(columns = {0:col})
        r_den = pd.concat([r_den, r_den_col], axis = 1)
    r = r_num/r_den
    return r

def get_corr_matrix(code, years, groups, modules, merger_date, test_brand_code = '568830', pre_months = 24, post_months = 24, brandnumber = 10, upcCutoff = 0.96):

    dt = datetime.strptime(merger_date, '%Y-%m-%d')
    month_int = dt.year * 12 + dt.month
    min_year, min_month = aux.int_to_month(month_int - pre_months)
    max_year, max_month = aux.int_to_month(month_int + post_months)

    brand_data_list = []
    product_map = aux.get_product_map(list(set(groups)))
    print(timeit.default_timer())

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
    
    print(timeit.default_timer())
        
    brand_data = pd.concat(brand_data_list).dropna(subset=['price']).drop_duplicates()
    brand_data = brand_data.pivot_table(index = 'store-week', columns = 'upc', values = 'price', aggfunc = 'first')
    print(brand_data)
    corr = vcorrcoef(brand_data)
    print(corr)
    print(timeit.default_timer())
    corr.to_csv('../../../All/m_' + code + '/intermediate/' + test_brand_code + '_corr_v2.csv', sep = ',')
    
    upper_corr = corr.where(np.triu(np.ones(corr.shape)).astype(np.bool))
    corr_upcs_list = []
    for col in upper_corr:
        for i, row_value in upper_corr[col].iteritems():
            if upper_corr.loc[i, col] > upcCutoff:
                corr_upcs_list.append((i, col, len(brand_data[[i, col]].dropna())))
    corr_upcs = pd.DataFrame(corr_upcs_list, columns = ['brand_1','brand_2', 'n_rows_without_missing_value'])
    print(timeit.default_timer())
    corr_upcs.to_csv('../../../All/m_' + code + '/intermediate/' + test_brand_code + '_correlated_upcs_v2.csv', sep = ',')

code = sys.argv[1]
test_brand_code = sys.argv[2]
if not os.path.isdir('../../../All/m_' + code + '/output'):
	os.makedirs('../../../All/m_' + code + '/output')
log_out = open('../../../All/m_' + code + '/output/get_corr_matrix_v2.log', 'w')
log_err = open('../../../All/m_' + code + '/output/get_corr_matrix_v2.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = aux.parse_info(code)

merger_date = info_dict['DateCompleted']
groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

get_corr_matrix(code, years, groups, modules, merger_date, test_brand_code)

log_out.close()
log_err.close()