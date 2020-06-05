import sys
import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import unicodecsv as csv 
import auxiliary as aux

def append_owners(code, df):
	upcs = pd.read_csv('m_' + code + '/intermediate/upcs.csv', delimiter = ',', index_col = 'upc')
	upcs = upcs['brand_code_uc']
	upc_map = upcs.to_dict()

	df['brand_code_uc'] = df['upc'].map(upc_map['brand_code_uc'])

	brand_to_owner = pd.read_csv('m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')

	FINISH THIS WITH NEW FORMAT!!

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
	YINTIAN/AISLING -- need to do this part

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

def did(df, merging_date, merging_parties, month_or_quarter = 'month'):
	# Add the necessary stuff
	df = add_dhhi(df)
	df['dma_upc'] = df['dma_code'].astype(str) + "_" + df['upc'].astype(str)
    df['lprice'] = np.log(df['price'])
    df['post_merger'] = ???
    df['merging'] = df['owner'].isin(merging_parties)

    if month_or_quarter == 'month':
    	df['trend'] = SOMETHING
    else:
    	df['trend'] = SOMETHING

    data = data.set_index(['dma_upc', month_or_quarter])

    with open('m_' + code + '/output/did_' + month_or_quarter + '.csv', "wb") as csvfile:
    	header = ["post_merger*merging", "post_merger*merging_se", "post_merger", "post_merger_se", "trend", "trend_se", OTHER STUFF???, "N", "r2", "product", "time"]
		writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
		writer.writerow(header)

	    # Run the various regressions
	    exog_vars = ['post_merger*merging', 'post_merger', 'trend']
	    exog = sm.add_constant(data[exog_vars])
	    mod = PanelOLS(data['lprice'], exog, entity_effects = False, time_effects = False)
	    reg_nofe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
	    PUT RESULTS INTO A LIST AND WRITE 

	    mod = PanelOLS(data['lprice'], data[exog_vars], entity_effects = True, time_effects = False)
	    reg_dma_product_fe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])

	    mod = PanelOLS(data['lprice'], data['post_merger*merging'], entity_effects = True, time_effects = True)
	    reg_time_fe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])

	    ADD IN DHHI INTERACTION

	    # Redo with demographics?

	    # Should we think about a case where we do a dummy for the second-largest firm too?


code = sys.argv[1]
info_dict = aux.parse_info(code)
merging_parties = aux.get_merging_parties(info_dict["MergingParties"])

for timetype in ['month', 'quarter']:
	df = pd.read_csv('m_' + code + '/intermediate/data_' + timetype + '.csv', delimiter = ',')
	df = append_owners(code, df)
	did(df, info_dict["DateCompleted"], merging_parties, timetype)


# Run DID for mo