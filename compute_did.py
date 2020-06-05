import sys
import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np

def append_owners(code, df):
	upcs = pd.read_csv('m_' + code + '/intermediate/upcs.csv', delimiter = ',', index_col = 'upc')
	upcs = upcs['brand_code_uc']
	upc_map = upcs.to_dict()

	df['brand_code_uc'] = df['upc'].map(upc_map['brand_code_uc'])

	brand_to_owner = pd.read_csv('m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')

def compute_hhi_map(df, owner_col = 'owner'):
	# df should have dma, upc, owner
	df = df[['dma', 'shares', owner_col]]
	df = df.groupby(['dma', owner_col]).sum()

	df['shares2'] = df['shares'] * df['shares']
	df = df.groupby('dma').sum()
	df = df.rename(columns = {'shares2' : 'hhi'})
	df = df[['dma', 'hhi']]
	df = df.set_index('dma')
	hhi_map = df.to_dict()
	return hhi_map

def add_dhhi(df):
	# First get inside upc shares at the DMA level in the pre period
	YINTIAN/AISLING

	# First get inside HHI pre at the dma level.
	pre_hhi_map = compute_hhi_map(df[['dma', 'shares', 'owner']])
	df['pre_hhi'] = df['dma'].map(pre_hhi_map['hhi'])

	# Then map to ownership post.
	#     (1) Read in ownership.csv
	#     (2) Just keep the month right after the merger (or maybe 3 months or so)
	#     (3) Use a map to generate ownership_post
	brand_to_new_owner = pd.read_csv('m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')
	brand_to_new_owner = brand_to_new_owner[NEXT MONTH] # YINTIAN/AISLING -- FIX THIS!!!
	brand_to_new_owner_map = brand_to_new_owner.to_dict()
	df['new_owner'] = df['brand_code_uc'].map(brand_to_new_owner_map['owner'])

	post_hhi_map = compute_hhi_map(df[['dma', 'shares', 'new_owner']], owner_col = 'new_owner')
	df['post_hhi'] = df['dma'].map(post_hhi_map['hhi'])

	df['dhhi'] = df['post_hhi'] - df['pre_hhi']
	return df

def did(df):
	# Add the necessary stuff
	df = add_dhhi(df)
	data['dma_upc'] = data['dma_code'].astype(str) + "_" + data['upc'].astype(str)
    data['lprice_' + product] = np.log(data['price'])
    data['post_merger'] = ???
    data['merging'] = USE AS ISIN

    data = data.set_index(['dma_upc', TIME THING])

    # No FEs
    exog_vars = ['post_merger*merging', 'post_merger', 'trend']
    exog = sm.add_constant(data[exog_vars])
    print(data[exog_vars])
    mod = PanelOLS(data['lprice_' + product], exog, entity_effects = False)

    # Product-DMA FEs + No Time


    # Product-DMA FEs + Time FEs (No nonmerging then)


    # Product-DMA FEs + Time Trend


    # Should we think about a case where we do a dummy for the second-largest firm too?
