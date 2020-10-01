import sys
import pandas as pd
import numpy as np
from datetime import datetime
import auxiliary as aux

def compute_nodivest_dhhi_dma(df, code, merging_date, merging_parties, volume):

	# Pull merger year and merger month (or quarter)
	merger_month_or_quarter = merging_date.month
	merger_year = merging_date.year

	# First, create shares for pre-merger period at the DMA level
	df_pre = df.loc[(df['year'] < merger_year) | ((df['year'] == merger_year) & (df['month'] < merger_month_or_quarter))].copy()
	df_pre = df_pre.groupby(['upc','dma_code'])['sales','volume'].agg({'sales':'sum','volume':'sum'}).reset_index()

	if volume:
		df_pre['dma_volume'] = df_pre.groupby('dma_code')['volume'].transform('sum')
		df_pre['inside_share_vol'] = df_pre['volume']/df_pre['dma_volume']
		df_pre = df_pre[['upc','dma_code','inside_share_vol']]
		df_pre = df_pre.rename(columns = {'inside_share_vol' : 'shares'})
	else:
		df_pre['dma_sales'] = df_pre.groupby('dma_code')['sales'].transform('sum')
		df_pre['inside_share_sales'] = df_pre['sales']/df_pre['dma_sales']
		df_pre = df_pre[['upc','dma_code','inside_share_sales']]
		df_pre = df_pre.rename(columns = {'inside_share_sales' : 'shares'})

	# Define time period for ownership mapping
	if merger_month_or_quarter > 2:
		df_pre['month'] = merger_month_or_quarter - 2
		df_pre['year'] = merger_year
	elif merger_month_or_quarter == 2:
		df_pre['month'] = 12
		df_pre['year'] = merger_year - 1
	elif merger_month_or_quarter == 1:
		df_pre['month'] = 11
		df_pre['year'] = merger_year - 1

	# Append ownership
	df_pre_own = aux.append_owners(code, df_pre, 'month', add_dhhi = True)

	# Collapse to DMA-owner level and compute pre-period HHI
	df_pre_dma_owner = df_pre_own.groupby(['owner','dma_code']).agg({'shares':'sum'}).reset_index()
	df_pre_dma_owner['shares2'] = df_pre_dma_owner['shares'] * df_pre_dma_owner['shares']
	hhi_pre = df_pre_dma_owner.groupby(['dma_code']).agg({'shares2':'sum'}).reset_index()
	hhi_pre = hhi_pre.rename(columns = {'shares2' : 'hhi_pre'})

	# Add merging party indicator and compute post-period HHI
	df_post_dma_owner = df_pre_dma_owner.copy()
	df_post_dma_owner.loc[df_post_dma_owner['owner'].isin(merging_parties),'owner'] = 'MergedEntity'
	df_post_dma_owner = df_post_dma_owner.groupby(['owner','dma_code']).agg({'shares':'sum'}).reset_index()
	df_post_dma_owner['shares2'] = df_post_dma_owner['shares'] * df_post_dma_owner['shares']
	hhi_post = df_post_dma_owner.groupby(['dma_code']).agg({'shares2':'sum'}).reset_index()
	hhi_post = hhi_post.rename(columns = {'shares2' : 'hhi_post'})

	# Join pre/post HHI and compute DHHI
	dma_level = hhi_pre.merge(hhi_post, on='dma_code')
	dma_level['hhi_pre'] = dma_level['hhi_pre']*10000
	dma_level['hhi_post'] = dma_level['hhi_post']*10000
	dma_level['dhhi'] = dma_level['hhi_post'] - dma_level['hhi_pre']

	return(dma_level)

def compute_nodivest_dhhi_agg(df, code, merging_date, merging_parties, volume):

	# Pull merger year and merger month (or quarter)
	merger_month_or_quarter = merging_date.month
	merger_year = merging_date.year

	# First, create shares for pre-merger period at the national level
	df_pre = df.loc[(df['year'] < merger_year) | ((df['year'] == merger_year) & (df['month'] < merger_month_or_quarter))].copy()

	# Define time period for ownership mapping
	if merger_month_or_quarter > 2:
		df_pre['month'] = merger_month_or_quarter - 2
		df_pre['year'] = merger_year
	elif merger_month_or_quarter == 2:
		df_pre['month'] = 12
		df_pre['year'] = merger_year - 1
	elif merger_month_or_quarter == 1:
		df_pre['month'] = 11
		df_pre['year'] = merger_year - 1

	# Map ownership
	df_pre = aux.append_owners(code, df, 'month')

	# Compute shares
	if volume:
		df_pre['agg_volume'] = df_pre['volume'].sum()
		df_pre['inside_share_vol'] = df_pre['volume']/df_pre['agg_volume']
		df_pre = df_pre[['upc','owner','inside_share_vol']]
		df_pre = df_pre.rename(columns = {'inside_share_vol' : 'shares'})
	else:
		df_pre['agg_sales'] = df_pre['sales'].sum()
		df_pre['inside_share_sales'] = df_pre['sales']/df_pre['agg_sales']
		df_pre = df_pre[['upc','owner','inside_share_sales']]
		df_pre = df_pre.rename(columns = {'inside_share_sales' : 'shares'})

	# Compute pre-period HHI
	df_pre_owner = df_pre.groupby(['owner']).agg({'shares':'sum'}).reset_index()
	df_pre_owner['shares2'] = df_pre_owner['shares'] * df_pre_owner['shares']
	hhi_pre = df_pre_owner.agg({'shares2':'sum'})
	hhi_pre = pd.DataFrame({'hhi_pre': hhi_pre})
	hhi_pre['merger_code'] = code

	# Add merging party indicator
	df_post_owner = df_pre_owner.copy()
	df_post_owner.loc[df_post_owner['owner'].isin(merging_parties),'owner'] = 'MergedEntity'
	df_post_owner = df_post_owner.groupby(['owner']).agg({'shares':'sum'}).reset_index()
	df_post_owner['shares2'] = df_post_owner['shares'] * df_post_owner['shares']
	hhi_post = df_post_owner.agg({'shares2':'sum'})
	hhi_post = pd.DataFrame({'hhi_post': hhi_post})
	hhi_post['merger_code'] = code

	# Join pre/post HHI and compute DHHI
	agg_level = hhi_pre.merge(hhi_post, on='merger_code')
	agg_level['hhi_pre'] = agg_level['hhi_pre']*10000
	agg_level['hhi_post'] = agg_level['hhi_post']*10000
	agg_level['dhhi'] = agg_level['hhi_post'] - agg_level['hhi_pre']

	return(agg_level)

def get_dma_map(year):

	# Import store file
	store_path = "../../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
	store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")

	# Keep unique DMA/DMA descriptions and send to dictionary
	dmas_descr = store_table[['dma_code','dma_descr']]
	dmas_descr = dmas_descr.drop_duplicates()
	dmas_descr.set_index('dma_code')
	dma_descr_map = dmas_descr.to_dict()
	return(dma_descr_map)

code_list = sys.argv[1].split(',')
volume = sys.argv[2]
log_out = open('../../../All/Validation/output/agency_validation.log', 'w')
log_err = open('../../../All/Validation/output/agency_validation.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

dma_descr_map = get_dma_map('2018')

hhi_agg_out = pd.DataFrame()
for code in code_list:

	df = pd.read_csv('../../../All/m_' + code + '/intermediate/data_month.csv', delimiter = ',')

	info_dict = aux.parse_info(code)
	dt = datetime.strptime(info_dict["DateCompleted"], '%Y-%m-%d')
	merging_parties = aux.get_parties(info_dict["MergingParties"])

	hhi_dma_out = compute_nodivest_dhhi_dma(df, code, dt, merging_parties, volume)
	hhi_dma_out['dma_descr'] = hhi_dma_out['dma_code'].map(dma_descr_map)
	hhi_dma_out = hhi_dma_out[['dma_code','dma_descr','hhi_pre','hhi_post','dhhi']]

	if volume:
		hhi_dma_out.to_csv('../../../All/Validation/valid_vol_m_' + code + '.csv', index = False, sep = ',', encoding = 'utf-8')
	else:
		hhi_dma_out.to_csv('../../../All/Validation/valid_sales_m_' + code + '.csv', index = False, sep = ',', encoding = 'utf-8')

	hhi_agg = compute_nodivest_dhhi_agg(df, code, dt, merging_parties, volume)
	hhi_agg_out = hhi_agg_out.append(hhi_agg)

hhi_agg_out = hhi_agg_out[['merger_code','hhi_pre','hhi_post','dhhi']]
if volume:
	hhi_agg_out.to_csv('../../../All/Validation/valid_vol_agg.csv', index = False, sep = ',', encoding = 'utf-8')
else:
	hhi_agg_out.to_csv('../../../All/Validation/valid_sales_agg.csv', index = False, sep = ',', encoding = 'utf-8')
