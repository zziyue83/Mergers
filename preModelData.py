import pandas as pd
import sys
import numpy as np
from linearmodels import PanelOLS

def BrandOwner(product):
    brand_owner = pd.read_excel("Top 100 " + product + " with owner.xlsx",header = 0,index_col=0)
    brand_owner_stacked = brand_owner.stack()
    brand_owner_stacked = brand_owner_stacked.reset_index(level=1)
    brand_owner_stacked.rename(columns={'level_1':'year', 0:'owner company'}, inplace=True)
    brand_owner_stacked = brand_owner_stacked.set_index('year', append=True)
    return brand_owner_stacked

def preModelData(product):
    panel_data = pd.DataFrame()
    upc_brand = pd.DataFrame()
    years = [2006, 2007, 2008, 2009]
    for year in years:
        year = str(year)
        chunks = pd.read_csv("../../GeneratedData/" + product + "_dma_month_upc_" + year + ".tsv", delimiter = "\t", chunksize = 1000000)
        for data_chunk in chunks:
            upc_brand = pd.concat([upc_brand, data_chunk[['upc','brand_descr']].set_index('upc')]).groupby(level=0).agg({'brand_descr': 'first'})
            print(upc_brand)
            data_chunk['Qtr'] = pd.to_datetime(data_chunk['month'].values, format='%Y%m').astype('period[Q]')
            panel_data_chunk = data_chunk.groupby(['upc','dma_code','Qtr']).agg({'volume': 'sum', 'price': ['count','sum']})
            if panel_data.empty:
                panel_data = panel_data_chunk
            else:
                panel_data = panel_data.add(panel_data_chunk, fill_value=0)
            print(panel_data)


    panel_data['avgprice'] = panel_data[('price','sum')]/panel_data[('price','count')]
    panel_data = panel_data.droplevel(level=1, axis=1).drop('price', axis=1)
    panel_data['log_price'] = np.log(panel_data['avgprice'])
    market_size = panel_data.reset_index('upc')
    market_size = market_size.groupby(level=[0,1]).agg({'volume': 'sum'})
    market_size_dma = market_size.groupby(level=0).agg({'volume': 'max'})*1.5
    panel_data['market share'] = market_size_dma['volume'].div(panel_data['volume'], level=1, fill_value=0)
    panel_data = panel_data.reset_index()
    panel_data['year'] = panel_data['Qtr'].dt.year
    panel_data['# quarter'] = panel_data['Qtr'].dt.quarter
    panel_data['postmerger'] = np.where((panel_data['year']==2006) | (panel_data['year']==2007) | ((panel_data['year']==2008) & (panel_data['# quarter'] == 1)), 0, 1)
    panel_data['brand_descr'] = panel_data['upc'].map(upc_brand['brand_descr'])
    brand_owner_stacked = BrandOwner(product)
    panel_data = panel_data.join(brand_owner_stacked, on=['brand_descr','year']).fillna(value='unknown')
    quarters_since_start_dictionary = {'2006Q1': 0, '2006Q2': 1, '2006Q3': 2, '2006Q4': 3, '2007Q1': 4, '2007Q2': 5, '2007Q3': 6, '2007Q4': 7, '2008Q1': 8, '2008Q2': 9, '2008Q3': 10, '2008Q4': 11, '2009Q1': 12, '2009Q2': 13, '2009Q3': 14, '2009Q4': 15}
    panel_data['quarters_since_start'] = panel_data['Qtr'].astype(str).map(quarters_since_start_dictionary)
    involvedbrands_list = list(set(panel_data['upc'][((panel_data['year']==2008) & (panel_data['owner company']=='Mars')) | ((panel_data['year']==2009) & (panel_data['owner company']=='Mars'))]))
    panel_data['involved'] = np.where(panel_data['upc'].isin(involvedbrands_list), 1, 0)
    print(panel_data)
    panel_data.to_csv("../../GeneratedData/panel_data_"+product+".tsv", sep = '\t', encoding = 'utf-8')
    panel_data = panel_data.set_index(['upc','dma_code'])
    panel_data.index = panel_data.index.get_level_values(0).astype(str) + ' ' + panel_data.index.get_level_values(1).astype(str)
    panel_data = panel_data.set_index('quarters_since_start', append = True, drop = False)
    print(panel_data)
    mod1 = PanelOLS.from_formula('log_price ~ 1 + involved*postmerger + postmerger + quarters_since_start + EntityEffects', data = panel_data, drop_absorbed=True)
    print(mod1.fit())
    
product = sys.argv[1]
preModelData(product)
