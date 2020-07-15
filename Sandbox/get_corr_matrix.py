import sys
from datetime import datetime
import auxiliary as aux
from tqdm import tqdm
import os
import pandas as pd
import numpy as np
import numba
import time

'''def get_den(u):
    n = len(u)
    z = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i > j:
                z[i, j] = z[j, i]
            else:
                z[i, j] = np.sqrt(u[i]*u[j])
                
    return z

def corr(df):
    start = time.process_time()
    
    df = df.fillna(0)
    x_mean = np.mean(df,axis=0)
    r_num = np.transpose(df-x_mean).dot(df-x_mean)
    r_den = get_den(np.sum((df-x_mean)**2,axis=0))
    r = r_num/r_den

    process_time = time.process_time() - start
    print(process_time)

    return r'''


@numba.njit
def my_corr(u, min_periods = 50):
    m = u.shape[0]
    n = u.shape[1]
 
    z = np.zeros((n, n))
 
    for i in range(n):
        for j in range(n):
            if i == j:
                z[i, j] = 1.0
            elif i > j:
                z[i, j] = z[j, i]
            else:
                val = 0.0
                mean1 = 0.0
                mean2 = 0.0
                sq1 = 0.0
                sq2 = 0.0
                okay = 0
                for k in range(m):
                    if not np.isnan(u[k, i]) and not np.isnan(u[k, j]):
                        okay += 1
                        val += u[k, i] * u[k, j]
                        mean1 += u[k, i]
                        sq1 += u[k, i] * u[k, i]
                        mean2 += u[k, j]
                        sq2 += u[k, j] * u[k, j]
                if okay >= min_periods:
                    z[i, j] = (val - mean1 * mean2) / (((sq1 - mean1**2) * (sq2 - mean2**2)) ** 0.5)
                else:
                    z[i, j] = 0.0
 
    return z

def get_corr_matrix(code, years, groups, modules, merger_date, test_brand_code = '568830', pre_months = 24, post_months = 24, brandnumber = 10, upcCutoff = 0.96):

    dt = datetime.strptime(merger_date, '%Y-%m-%d')
    month_int = dt.year * 12 + dt.month
    min_year, min_month = aux.int_to_month(month_int - pre_months)
    max_year, max_month = aux.int_to_month(month_int + post_months)

    data_list = []
    product_map = aux.get_product_map(list(set(groups)))
    time_1 = time.process_time()
    print(time_1)

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
                data_chunk = data_chunk.dropna(subset=['price']).groupby(['upc','store-week','upc_ver_uc'], as_index = False).agg({'price': 'first'})
                data_list.append(data_chunk)
                
    data_df = pd.concat(data_list)
    data_df = data_df.join(product_map[['brand_code_uc']], on=['upc','upc_ver_uc'], how='left')
    data_df = data_df.groupby(['upc','store-week','brand_code_uc'], as_index = False).agg({'price': 'first'})
    data_df.to_csv('../../../All/m_' + code + '/intermediate/data_df.csv', sep = ',', index = False)
    time_2 = time.process_time()
    print(time_2 - time_1)
    
    brand_data_df = data_df[data_df['brand_code_uc'] == int(test_brand_code)]
    brand_data_df = brand_data_df[['upc','store-week','price']].drop_duplicates()
    brand_data_df = brand_data_df.pivot_table(index = 'store-week', columns = 'upc', values = 'price', aggfunc = 'first')
    print(brand_data_df)
    bd_numpy = brand_data_df.to_numpy()
    corr_numpy = my_corr(bd_numpy)
    corr = pd.DataFrame(corr_numpy, index = brand_data_df.columns, columns = brand_data_df.columns)
    # corr = brand_data_df.corr()
    print(corr)
    time_3 = time.process_time()
    print(time_3 - time_2)
    corr.to_csv('../../../All/m_' + code + '/intermediate/' + test_brand_code + '_corr.csv', sep = ',')

    upper_corr = corr.where(np.triu(np.ones(corr.shape)).astype(np.bool))
    corr_upcs_list = []
    for col in upper_corr:
        for i, row_value in upper_corr[col].iteritems():
            if upper_corr.loc[i, col] > upcCutoff:
                corr_upcs_list.append((i, col, len(brand_data_df[[i, col]].dropna())))
    corr_upcs = pd.DataFrame(corr_upcs_list, columns = ['brand_1','brand_2', 'n_rows_without_missing_value'])
    corr_upcs = corr_upcs[corr_upcs['brand_1'] != corr_upcs['brand_2']]
    print(time.process_time() - time_3)
    corr_upcs.to_csv('../../../All/m_' + code + '/intermediate/' + test_brand_code + '_correlated_upcs.csv', sep = ',', index = False)

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
test_brand_code = sys.argv[2]
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

get_corr_matrix(code, years, groups, modules, merger_date, test_brand_code)

log_out.close()
log_err.close()