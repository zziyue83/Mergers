import sys
from datetime import datetime
import auxiliary as aux
from tqdm import tqdm
import os
import pandas as pd
import numpy as np
import time

def get_corr_matrix(code, years, groups, modules, merger_date, upcCutoff = '0.96', pre_months = 24, post_months = 24, brand_number = 10):

    dt = datetime.strptime(merger_date, '%Y-%m-%d')
    month_int = dt.year * 12 + dt.month
    min_year, min_month = aux.int_to_month(month_int - pre_months)
    max_year, max_month = aux.int_to_month(month_int + post_months)

    corr_upcs_list = []
    product_map = aux.get_product_map(list(set(groups)))
    time_1 = time.process_time()
    print(time_1)

    brands_df = pd.read_csv('../../../All/m_' + code + '/intermediate/brands.csv').sort_values(by='overall_brand_share',ascending=False)
    brand_code_set = brands_df.head(brand_number)['brand_code_uc']
    brand_code_set = [int(i) for i in brand_code_set]

    for group, module in zip(groups, modules):
        upcs_list = []
        for year in years:
            module_data_list = []
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

            module_data_df = pd.concat(module_data_list)
            time_2 = time.process_time()
            print(time_2 - time_1)
            
            for brand_code in brand_code_set:
                time_3 = time.process_time()
                brand_data_df = module_data_df[module_data_df['brand_code_uc'] == brand_code]
                if len(brand_data_df) > 0:
                    try:
                        brand_data_df = brand_data_df.groupby(['upc','store-week'], as_index = False).agg({'price':'first'})
                        brand_data_df = brand_data_df.pivot_table(index = 'store-week', columns = 'upc', values = 'price', aggfunc = 'first')
                        corr = brand_data_df.corr(min_periods=50).reset_index().rename(columns={'upc':'upc_1'})
                        time_4 = time.process_time()
                        print('corr computation time')
                        print(time_4 - time_3)
                        corr_unpivoted = corr.melt(id_vars=['upc_1'], var_name='upc_2', value_name='correlation')
                        print(corr_unpivoted)
                        df = pd.concat([corr_unpivoted, pd.DataFrame(np.sort(corr_unpivoted[['upc_1','upc_2']], axis=1))], axis=1)
                        print(df)
                        df = df.drop_duplicates(df.columns.difference(corr_unpivoted.columns))[corr_unpivoted.columns]
                        print(df)
                        df = df.dropna(subset=['correlation'])
                        print(df)
                        upc_brand_year = df[df['upc_1'] != df['upc_2']]
                        print(upc_brand_year)
                        upc_brand_year['brand_code'] = brand_code
                        upc_brand_year['year'] = year
                        upc_brand_year['group'] = group
                        upc_brand_year['module'] = module
                        if not os.path.isfile('../../../All/m_' + code + '/intermediate/upcs_corr_intermediate.csv'):
                            upc_brand_year.to_csv('../../../All/m_' + code + '/intermediate/upcs_corr_intermediate.csv', sep = ',', index = False)
                        else:
                            upc_brand_year.to_csv('../../../All/m_' + code + '/intermediate/upcs_corr_intermediate.csv', mode='a', header=False, index = False)
                        print(time.process_time() - time_4)
                        upcs_list.append(upc_brand_year)
                    except:
                        brand_data_df.to_csv('../../../All/m_' + code + '/intermediate/' + str(brand_code) + '_unstacked_error.csv', sep = ',', index = False)
                        print(' ')
                        print('error')
                        print(len(brand_data_df))
                        print(brand_data_df.head())
                        print(' ')

        if len(upcs_list) > 0:
            upcs_df = pd.concat(upcs_list)
            print(upcs_df)
            min_upcs = upcs_df.groupby(['upc_1','upc_2','brand_code'], as_index = False).agg({'group': 'first', 'module': 'first', 'correlation': 'min'})
            corr_upcs = min_upcs[min_upcs['correlation'] > float(corrCutoff)]
            corr_upcs_list.append(corr_upcs)

    corr_df = pd.concat(corr_upcs_list)
    print(corr_df)
    corr_df.to_csv('../../../All/m_' + code + '/intermediate/correlated_upcs_' + corrCutoff + '_cutoff.csv', sep = ',', index = False)

code = sys.argv[1]
corrCutoff = sys.argv[2]
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

# get_corr_matrix(code, years, groups, modules, merger_date, test_brand_code)
get_corr_matrix(code, years, groups, modules, merger_date, corrCutoff)

log_out.close()
log_err.close()