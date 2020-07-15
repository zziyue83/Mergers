import sys
from tqdm import tqdm
import numpy as np
import pandas as pd
import auxiliary as aux

def calculate_brand_share(code, groups, years, month_or_quarter = 'month'):
    data_df = pd.read_csv('../../../All/m_' + code + '/intermediate/data_' + month_or_quarter + '.csv')
    market_sizes = pd.read_csv('../../../All/m_' + code + '/intermediate/market_sizes.csv')[['dma_code','market_size']].drop_duplicates().set_index('dma_code')
    data_df['market_size'] = data_df['dma_code'].map(market_sizes['market_size'])
    data_df['volume'] = data_df['market_size']*data_df['shares']
    upc_ver_agg = {}
    for year in years:
        upc_ver_map = aux.get_upc_ver_uc_map(year)
        upc_ver_agg.update(upc_ver_map)
    data_df['upc_ver_uc'] = data_df['upc'].map(upc_ver_agg)
    product_map = aux.get_product_map(list(set(groups)))
    data_df = data_df.join(product_map[['brand_code_uc', 'brand_descr']], on=['upc','upc_ver_uc'], how='left')
    brand_shares = data_df.groupby(['brand_code_uc', 'brand_descr'], as_index = False).agg({'volume': 'sum', 'market_size': 'sum'})
    brand_shares['brand_share'] = brand_shares['volume']/brand_shares['market_size']
    #brand_shares.to_csv('../../../All/m_' + code + '/intermediate/brand_shares.csv', sep = ',', encoding = 'utf-8')
    return brand_shares

code = sys.argv[1]
log_out = open('../../../All/m_' + code + '/output/calculate_brand_share.log', 'w')
log_err = open('../../../All/m_' + code + '/output/calculate_brand_share.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])
calculate_brand_share(code, groups, years)

log_out.close()
log_err.close()



