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
                
    return z'''

'''def corr(df):
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
                sum1 = 0.0
                sum2 = 0.0
                sq1 = 0.0
                sq2 = 0.0
                okay = 0
                for k in range(m):
                    if not np.isnan(u[k, i]) and not np.isnan(u[k, j]):
                        okay += 1
                        val += u[k, i] * u[k, j]
                        sum1 += u[k, i]
                        sq1 += u[k, i] * u[k, i]
                        sum2 += u[k, j]
                        sq2 += u[k, j] * u[k, j]
                if okay >= min_periods:
                    if ((okay * sq1 - sum1**2) * (okay * sq2 - sum2**2)) ** 0.5 == 0:
                        if ((okay * sq1 - sum1**2) == (okay * sq2 - sum2**2)) & (sum1 == sum2):
                            z[i, j] = 1.0
                        else:
                            z[i, j] = 0.0
                    else:
                        z[i, j] = (okay * val - sum1 * sum2) / (((okay * sq1 - sum1**2) * (okay * sq2 - sum2**2)) ** 0.5)
                else:
                    z[i, j] = 0.0
    return z


#@numba.njit
'''
def test_corr(u, min_periods = 20):
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
                sum1 = 0.0
                sum2 = 0.0
                sq1 = 0.0
                sq2 = 0.0
                okay = 0
                for k in range(m):
                    if not np.isnan(u[k, i]) and not np.isnan(u[k, j]):
                        okay += 1
                        val += u[k, i] * u[k, j]
                        sum1 += u[k, i]
                        sq1 += u[k, i] * u[k, i]
                        sum2 += u[k, j]
                        sq2 += u[k, j] * u[k, j]
                if okay >= min_periods:
                    den = (((okay * sq1 - sum1**2) * (okay * sq2 - sum2**2)) ** 0.5)
                    if den == 0:
                        print('okay')
                        print(okay)
                        print('sq1')
                        print(sq1)
                        print('sq2')
                        print(sq2)
                        print('sum1')
                        print(sum1)
                        print('sum2')
                        print(sum2)
                        print(den)
                        print(okay * val - sum1 * sum2)
                        return den
'''

def get_corr_matrix(code, years, groups, modules, merger_date, pre_months = 24, post_months = 24, brand_number = 10, upcCutoff = 0.96):

    dt = datetime.strptime(merger_date, '%Y-%m-%d')
    month_int = dt.year * 12 + dt.month
    min_year, min_month = aux.int_to_month(month_int - pre_months)
    max_year, max_month = aux.int_to_month(month_int + post_months)

    min_corr_upcs_list = []
    product_map = aux.get_product_map(list(set(groups)))
    time_1 = time.process_time()
    print(time_1)

    brands_df = pd.read_csv('../../../All/m_' + code + '/intermediate/brands.csv').sort_values(by='overall_brand_share',ascending=False)
    brand_code_set = brands_df.head(brand_number)['brand_code_uc']
    brand_code_set = [int(i) for i in brand_code_set]

    for group, module in zip(groups, modules):
        module_data_list = []
        corr_upcs_list = []
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
                data_chunk = data_chunk[data_chunk.brand_code_uc.isin(brand_code_set)]
                data_chunk = data_chunk.dropna(subset=['price']).groupby(['upc','store-week','upc_ver_uc'], as_index = False).agg({'price': 'first', 'brand_code_uc': 'first'})
                module_data_list.append(data_chunk)
                print(module_data_list[0])
        
            module_data_df = pd.concat(module_data_list)
            print('aggregated at the year level')
            print(module_data_df.head())
            time_2 = time.process_time()
            print(time_2 - time_1)
            
            for brand_code in brand_code_set:
                time_3 = time.process_time()
                brand_data_df = module_data_df[module_data_df['brand_code_uc'] == brand_code]
                try:
                    brand_data_df = brand_data_df.groupby(['upc','store-week'], as_index = False).agg({'price':'first'})
                    print(brand_data_df)
                    brand_data_df = brand_data_df.pivot_table(index = 'store-week', columns = 'upc', values = 'price', aggfunc = 'first')
                    print(brand_data_df)
                    '''
                    bd_numpy = brand_data_df.to_numpy()
                    try:
                        corr_numpy = my_corr(bd_numpy)
                    except:
                        error = test_corr(bd_numpy)
                        assert error != 0, "division error"
                    corr_numpy = my_corr(bd_numpy)
                    corr = pd.DataFrame(corr_numpy, index = brand_data_df.columns, columns = brand_data_df.columns)
                    '''
                    corr = brand_data_df.corr(min_periods=50)
                    print(corr)
                    time_4 = time.process_time()
                    print('corr computation time')
                    print(time_4 - time_3)
                    upper_corr = corr.where(np.triu(np.ones(corr.shape)).astype(np.bool))
                    corr_brand_upcs_list = []
                    for col in upper_corr:
                        for i, row_value in upper_corr[col].iteritems():
                            if i != col:
                                if upper_corr.loc[i, col] > upcCutoff:
                                    corr_brand_upcs_list.append((i, col, upper_corr.loc[i, col], brand_code, group, module))
                    corr_brand_upcs = pd.DataFrame(corr_brand_upcs_list, columns = ['upc_1','upc_2', 'correlation', 'brand_code_uc', 'group', 'module'])
                    print(time.process_time() - time_4)
                    corr_upcs_list.append(corr_brand_upcs)
                except:
                    brand_data_df.to_csv('../../../All/m_' + code + '/output/' + str(brand_code) + '_unstacked_error.csv', sep = ',', index = False)
                    print(' ')
                    print('error')
                    print(len(brand_data_df))
                    print(brand_data_df.head())
                    print(' ')
            
        corr_upcs = pd.concat(corr_upcs_list)
        print(corr_upcs)
        min_corr_upcs = corr_upcs.groupby(['upc_1','upc_2','brand_code_uc'], as_index = False).agg({'group': 'first', 'module': 'first', 'correlation': 'min'})
        min_corr_upcs_list.append(min_corr_upcs)
    
    corr_df = pd.concat(min_corr_upcs_list)
    print(corr_df)
    corr_df = corr_df.groupby(['upc_1','upc_2','brand_code_uc','group','module'], as_index = False).agg({'correlation': 'min'})
    print(corr_df)
    corr_df = corr_df[corr_df['correlation'] > upcCutoff]
    print(corr_df)
    corr_df.to_csv('../../../All/m_' + code + '/intermediate/correlated_upcs_v2.csv', sep = ',', index = False)

code = sys.argv[1]
# test_brand_code = [sys.argv[2]]
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

# get_corr_matrix(code, years, groups, modules, merger_date, test_brand_code)
get_corr_matrix(code, years, groups, modules, merger_date)

log_out.close()
log_err.close()