import sys
import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import unicodecsv as csv
import auxiliary as aux
from datetime import datetime

def append_aggregate_demographics(df, month_or_quarter):

	# Load agent data
	agent_data = pd.read_csv('master/agent_data_' + month_or_quarter + '.csv', delimiter = ',')

	# Per-person income
	agent_data['hhinc_per_person'] = agent_data['HINCP_ADJ'] / agent_data['hhmember']

	# Compute mean demographics by DMA and month or quarter
	dma_stats = agent_data.groupby(['year','dma_code'])['hhinc_per_person'].agg('median')
	demog_map = dma_stats.to_dict()

	# Map to main dataframe
	df['hhinc_per_person'] = df[['year','dma_code']].map(demog_map)

	return df

def compute_hhi_map(df, owner_col = 'owner'):

	# df should have dma, upc, owner, shares
	df = df[['dma_code', 'shares', owner_col]]
	df = df.groupby(['dma_code', owner_col]).sum()

	# Compute HHI
	df['shares2'] = df['shares'] * df['shares']
	df = df.groupby('dma_code').sum()
	df = df.rename(columns = {'shares2' : 'hhi'})
	print(df.head())
	df = df['hhi']
	hhi_map = df.to_dict()
	return hhi_map

def add_dhhi(df, merging_date, month_or_quarter):

	# Pull merger year and merger month (or quarter)
	if month_or_quarter == 'month':
		merger_month_or_quarter = merging_date.month
	elif month_or_quarter == 'quarter':
		merger_month_or_quarter = np.ceil(merging_date.month/3)
	merger_year = merging_date.year

	# First, create shares for pre-merger period at the DMA level
	df_pre = df.loc[(df['year'] < merger_year) | ((df['year'] == merger_year) & (df[month_or_quarter] < merger_month_or_quarter))].copy()
	print(df_pre.columns)
	df_pre = df_pre.groupby(['upc','dma_code'])['shares','brand_code_uc'].agg({'shares':'sum','brand_code_uc':'first'}).reset_index()
	df_pre['dma_share'] = df_pre.groupby('dma_code')['shares'].transform('sum') # We may want to generalize this. Right now, it assumes that market size is constant over time.
	df_pre['inside_share'] = df_pre['shares']/df_pre['dma_share']
	print(df_pre.columns)
	df_pre = df_pre[['upc','dma_code','inside_share']]
	df_pre = df_pre.rename(columns = {'inside_share' : 'shares'})

	if merger_month_or_quarter > 1:
		df_pre[month_or_quarter] = merger_month_or_quarter - 1
		df_pre['year'] = merger_year
	else:
		if month_or_quarter == 'month':
			df_pre[month_or_quarter] = 12
		elif month_or_quarter == 'quarter':
			df_pre[month_or_quarter] = 4
		df_pre['year'] = merger_year - 1

	print(df_pre.columns)
	df_pre_own = aux.append_owners(code, df_pre, month_or_quarter,add_dhhi = True)

	# Get inside HHI pre at the DMA level
	pre_hhi_map = compute_hhi_map(df_pre_own[['dma_code', 'shares', 'owner']])
	df['pre_hhi'] = df['dma_code'].map(pre_hhi_map)

	# Now, get owners post merger
	df_post = df_pre.copy()

	if month_or_quarter == 'month':
		if merger_month_or_quarter == 12:
			df_post['month'] = 1
		else:
			df_post['month'] = merger_month_or_quarter + 1
	elif month_or_quarter == 'quarter':
		if merger_month_or_quarter == 4:
			df_post['quarter'] = 1
		else:
			df_post['quarter'] = merger_month_or_quarter + 1

	df_post['year'] = merger_year

	df_post_own = aux.append_owners(code, df_post, month_or_quarter,add_dhhi= True)

	# Get inside HHI post at the DMA level
	post_hhi_map = compute_hhi_map(df_post_own[['dma_code', 'shares', 'owner']])
	df['post_hhi'] = df['dma_code'].map(post_hhi_map)

	# Compute DHHI and return
	df['dhhi'] = df['post_hhi'] - df['pre_hhi']

	return df

def write_overlap(code, df, merging_date, merging_parties, month_or_quarter = 'month'):

	# Pull merger year and merger month (or quarter)
	merging_date = datetime.strptime(merging_date, '%Y-%m-%d')
	merger_year = merging_date.year
	merger_month = merging_date.month
	if month_or_quarter == 'month':
		merger_month_or_quarter = merger_month
	elif month_or_quarter == 'quarter':
		merger_month_or_quarter = np.ceil(merger_month/3)
	
	# First get total sales in entire market pre and post
	ms = pd.read_csv('../../../All/m_' + code + '/intermediate/market_sizes.csv', delimiter = ',')
	ms['post_merger'] = 0
	ms.loc[(ms['year']>merger_year) | ((ms['year']==merger_year) & (ms['month']>=merger_month)), 'post_merger'] = 1

	total_sales_post = ms.total_sales[ms['post_merger'] == 1].sum()
	total_sales_pre = ms.total_sales[ms['post_merger'] == 0].sum()

	df['post_merger'] = 0
	df.loc[(df['year']>merger_year) | ((df['year']==merger_year) & (df[month_or_quarter]>=merger_month_or_quarter)),'post_merger'] = 1

	# Get a dataframe that is pre-sales, post-sales, pre-shares, post-shares for all merging parties
	rows_list = []
	for party in df.owner.unique():
		party_sales_pre = df.sales[(df['owner'] == party) & (df['post_merger'] == 0)].sum()
		party_sales_post = df.sales[(df['owner'] == party) & (df['post_merger'] == 1)].sum()
		party_share_pre = party_sales_pre / total_sales_pre
		party_share_post = party_sales_post / total_sales_post

		if party in merging_parties:
			is_merging_party = 1
		else:
			is_merging_party = 0

		this_dict = {'name' : party, 'pre_sales' : party_sales_pre, 'post_sales' : party_sales_post, 'pre_share' : party_share_pre, 'post_share' : party_share_post, 'merging_party' : is_merging_party}
		rows_list.append(this_dict)
	overlap_df = pd.DataFrame(rows_list)
	overlap_df = overlap_df.sort_values(by = 'merging_party', ascending = False)
	overlap_df.to_csv('../../../All/m_' + code + '/output/overlap.csv', sep = ',', encoding = 'utf-8')


def did(df, merging_date, merging_parties, month_or_quarter = 'month'):

	# Pull merger year and merger month (or quarter)
	if month_or_quarter == 'month':
		merger_month_or_quarter = merging_date.month
	elif month_or_quarter == 'quarter':
		merger_month_or_quarter = np.ceil(merging_date.month/3)
	merger_year = merging_date.year

	# Add DHHI, adjust for inflation, add DMA/UPC indicator, log price and post-merger indicator
	df = add_dhhi(df, merging_date, month_or_quarter)
	df = aux.adjust_inflation(df, ['hhinc_per_person'], month_or_quarter)
	df['dma_upc'] = df['dma_code'].astype(str) + "_" + df['upc'].astype(str)
	df['lprice'] = np.log(df['prices_adj'])
	df['post_merger'] = 0
	df.loc[(df['year']>merger_year) | ((df['year']==merger_year) & (df[month_or_quarter]>=merger_month_or_quarter)),'post_merger'] = 1
	df['merging'] = df['owner'].isin(merging_parties)

	min_year = df['year'].min()
	min_month_or_quarter = df[df['year'] == min_year, month_or_quarter].min()
	if month_or_quarter == 'month':
		num_periods = 12
	else:
		num_periods = 4
	df['trend'] = 0
	df.loc[df['year'] == min_year, 'trend'] = df[df['year'] == min_year, month_or_quarter] - min_month_or_quarter
	df.loc[df['year'] > min_year, 'trend'] = (num_periods - min_month_or_quarter) + num_periods * (df[df['year'] > min_year, 'year'] - min_year - 1) + df[df['year'] > min_year, month_or_quarter]

	df['time_index'] = df['year']*100 + df[month_or_quarter]
	data = df.set_index(['dma_upc', 'time_index'])

	# Add interaction terms
	data['post_merger_merging'] = data['post_merger']*data['merging']
	data['post_merger_dhhi'] = data['post_merger']*data['dhhi']

	# Add demographics
	data['log_hhinc_per_person_adj'] = np.log(data['hhinc_per_person_adj'])

	with open('../../../Data/m_' + code + '/output/did_' + month_or_quarter + '.csv', "wb") as csvfile:
		header = ["model","post_merger*merging", "post_merger*merging_se", "post_merger*merging_pval", "post_merger*dhhi", "post_merger*dhhi_se", "post_merger*dhhi_pval", "post_merger", "post_merger_se", "post_merger_pval", "trend", "trend_se", "trend_pval", "log_hhinc_per_person_adj", "log_hhinc_per_person_adj_se", "log_hhinc_per_person_adj_pval", "N", "r2", "product", "time"]
		writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
		writer.writerow(header)

		# Run the various regressions

		# No fixed effects
		exog_vars = ['post_merger_merging', 'post_merger', 'trend']
		exog = sm.add_constant(data[exog_vars])
		mod = PanelOLS(data['lprice'], exog, entity_effects = False, time_effects = False)
		reg_nofe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_nofe = ['No FE',str(reg_nofe.params[0]),str(reg_nofe.std_errors[0]), str(reg_nofe.pvalues[0]), \
			'','','', \
			str(reg_nofe.params[1]),str(reg_nofe.std_errors[1]),str(reg_nofe.pvalues[1]), \
			str(reg_nofe.params[2]),str(reg_nofe.std_errors[2]),str(reg_nofe.pvalues[2]), \
			'','','', \
			str(reg_nofe.nobs),str(reg_nofe.rsquared),'No','No']
		writer.writerow(res_nofe)

		# Product/market fixed effects
		mod = PanelOLS(data['lprice'], data[exog_vars], entity_effects = True, time_effects = False)
		reg_dma_product_fe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_dma_product_fe = ['DMA/Product FE',str(reg_dma_product_fe.params[0]),str(reg_dma_product_fe.std_errors[0]),str(reg_dma_product_fe.pvalues[0]), \
			'','','', \
			str(reg_dma_product_fe.params[1]),str(reg_dma_product_fe.std_errors[1]),str(reg_dma_product_fe.pvalues[1]), \
			str(reg_dma_product_fe.params[2]),str(reg_dma_product_fe.std_errors[2]),str(reg_dma_product_fe.pvalues[2]), \
			'','','', \
			str(reg_dma_product_fe.nobs),str(reg_dma_product_fe.rsquared),'Yes','No']
		writer.writerow(res_dma_product_fe)

		# Product/market and time fixed effects
		mod = PanelOLS(data['lprice'], data['post_merger_merging'], entity_effects = True, time_effects = True)
		reg_time_fe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_time_fe = ['Time FE',str(reg_time_fe.params[0]),str(reg_time_fe.std_errors[0]),str(reg_time_fe.pvalues[0]), \
			'','','','','','','','','','','','', \
			str(reg_time_fe.nobs),str(reg_time_fe.rsquared),'Yes','Yes']
		writer.writerow(res_time_fe)

		# No fixed effects, DHHI
		exog_vars_dhhi = ['post_merger_dhhi', 'post_merger', 'trend']
		exog_dhhi = sm.add_constant(data[exog_vars_dhhi])
		mod = PanelOLS(data['lprice'], exog_dhhi, entity_effects = False, time_effects = False)
		reg_nofe_dhhi = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_nofe_dhhi = ['No FE, DHHI','','','', \
			str(reg_nofe_dhhi.params[0]),str(reg_nofe_dhhi.std_errors[0]),str(reg_nofe_dhhi.pvalues[0]), \
			str(reg_nofe_dhhi.params[1]),str(reg_nofe_dhhi.std_errors[1]),str(reg_nofe_dhhi.pvalues[1]), \
			str(reg_nofe_dhhi.params[2]),str(reg_nofe_dhhi.std_errors[2]),str(reg_nofe_dhhi.pvalues[2]), \
			'','','', \
			str(reg_nofe_dhhi.nobs),str(reg_nofe_dhhi.rsquared),'No','No']
		writer.writerow(res_nofe_dhhi)

		# Product/market fixed effects, DHHI
		mod = PanelOLS(data['lprice'], exog_vars_dhhi, entity_effects = True, time_effects = False)
		reg_dma_product_fe_dhhi = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_dma_product_fe_dhhi = ['DMA/Product FE, DHHI','','','', \
			str(reg_dma_product_fe_dhhi.params[0]),str(reg_dma_product_fe_dhhi.std_errors[0]),str(reg_dma_product_fe_dhhi.pvalues[0]), \
			str(reg_dma_product_fe_dhhi.params[1]),str(reg_dma_product_fe_dhhi.std_errors[1]),str(reg_dma_product_fe_dhhi.pvalues[1]), \
			str(reg_dma_product_fe_dhhi.params[2]),str(reg_dma_product_fe_dhhi.std_errors[2]),str(reg_dma_product_fe_dhhi.pvalues[2]), \
			'','','', \
			str(reg_dma_product_fe_dhhi.nobs),str(reg_dma_product_fe_dhhi.rsquared),'Yes','No']
		writer.writerow(res_dma_product_fe_dhhi)

		# Product/market and time fixed effects, DHHI
		mod = PanelOLS(data['lprice'], data['post_merger_dhhi'], entity_effects = True, time_effects = True)
		reg_time_fe_dhhi = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_time_fe_dhhi = ['Time FE, DHHI','','','', \
			str(reg_time_fe_dhhi.params[0]),str(reg_time_fe_dhhi.std_errors[0]),str(reg_time_fe_dhhi.pvalues[0]), \
			'','','','','','','','','', \
			str(reg_time_fe_dhhi.nobs),str(reg_time_fe_dhhi.rsquared),'Yes','Yes']
		writer.writerow(res_time_fe_dhhi)

		# No fixed effects, demographics
		exog_vars = ['post_merger_merging', 'post_merger', 'trend', 'log_hhinc_per_person_adj']
		exog = sm.add_constant(data[exog_vars])
		mod = PanelOLS(data['lprice'], exog, entity_effects = False, time_effects = False)
		reg_nofe_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_nofe_demog = ['No FE, Demographics',str(reg_nofe_demog.params[0]),str(reg_nofe_demog.std_errors[0]),str(reg_nofe_demog.pvalues[0]), \
			'','','', \
			str(reg_nofe_demog.params[1]),str(reg_nofe_demog.std_errors[1]),str(reg_nofe_demog.pvalues[1]), \
			str(reg_nofe_demog.params[2]),str(reg_nofe_demog.std_errors[2]),str(reg_nofe_demog.pvalues[2]), \
			str(reg_nofe_demog.params[3]),str(reg_nofe_demog.std_errors[3]),str(reg_nofe_demog.pvalues[3]), \
			str(reg_nofe_demog.nobs),str(reg_nofe_demog.rsquared),'No','No']
		writer.writerow(res_nofe_demog)

		# Product/market fixed effects, demographics
		mod = PanelOLS(data['lprice'], data[exog_vars], entity_effects = True, time_effects = False)
		reg_dma_product_fe_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_dma_product_fe_demog = ['DMA/Product FE, Demographics',str(reg_dma_product_fe_demog.params[0]),str(reg_dma_product_fe_demog.std_errors[0]),str(reg_dma_product_fe_demog.pvalues[0]), \
			'','','', \
			str(reg_dma_product_fe_demog.params[1]),str(reg_dma_product_fe_demog.std_errors[1]),str(reg_dma_product_fe_demog.pvalues[1]), \
			str(reg_dma_product_fe_demog.params[2]),str(reg_dma_product_fe_demog.std_errors[2]),str(reg_dma_product_fe_demog.pvalues[2]), \
			str(reg_dma_product_fe_demog.params[3]),str(reg_dma_product_fe_demog.std_errors[3]),str(reg_dma_product_fe_demog.pvalues[3]), \
			str(reg_dma_product_fe_demog.nobs),str(reg_dma_product_fe_demog.rsquared),'Yes','No']
		writer.writerow(res_dma_product_fe_demog)

		# Product/market and time fixed effects, demographics
		mod = PanelOLS(data['lprice'], data[['post_merger_merging','log_hhinc_per_person_adj']], entity_effects = True, time_effects = True)
		reg_time_fe_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_time_fe_demog = ['Time FE, Demographics',str(reg_time_fe_demog.params[0]),str(reg_time_fe_demog.std_errors[0]),str(reg_time_fe_demog.pvalues[0]), \
			'','','','','','','','','', \
			str(reg_time_fe_demog.params[1]),str(reg_time_fe_demog.std_errors[1]),str(reg_time_fe_demog.pvalues[1]), \
			str(reg_time_fe_demog.nobs),str(reg_time_fe_demog.rsquared),'Yes','Yes']
		writer.writerow(res_time_fe_demog)

		# No fixed effects, DHHI, demographics
		exog_vars_dhhi = ['post_merger_dhhi', 'post_merger', 'trend', 'log_hhinc_per_person_adj']
		exog_dhhi = sm.add_constant(data[exog_vars_dhhi])
		mod = PanelOLS(data['lprice'], exog_dhhi, entity_effects = False, time_effects = False)
		reg_nofe_dhhi_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_nofe_dhhi_demog = ['No FE, DHHI, Demographics','','','', \
			str(reg_nofe_dhhi_demog.params[0]),str(reg_nofe_dhhi_demog.std_errors[0]),str(reg_nofe_dhhi_demog.pvalues[0]), \
			str(reg_nofe_dhhi_demog.params[1]),str(reg_nofe_dhhi_demog.std_errors[1]),str(reg_nofe_dhhi_demog.pvalues[1]), \
			str(reg_nofe_dhhi_demog.params[2]),str(reg_nofe_dhhi_demog.std_errors[2]),str(reg_nofe_dhhi_demog.pvalues[2]), \
			str(reg_nofe_dhhi_demog.params[3]),str(reg_nofe_dhhi_demog.std_errors[3]),str(reg_nofe_dhhi_demog.pvalues[3]), \
			str(reg_nofe_dhhi_demog.nobs),str(reg_nofe_dhhi_demog.rsquared),'No','No']
		writer.writerow(res_nofe_dhhi_demog)

		# Product/market fixed effects, DHHI, demographics
		mod = PanelOLS(data['lprice'], exog_vars_dhhi, entity_effects = True, time_effects = False)
		reg_dma_product_fe_dhhi_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_dma_product_fe_dhhi_demog = ['DMA/Product FE, DHHI, Demographics','','','', \
			str(reg_dma_product_fe_dhhi_demog.params[0]),str(reg_dma_product_fe_dhhi_demog.std_errors[0]),str(reg_dma_product_fe_dhhi_demog.pvalues[0]), \
			str(reg_dma_product_fe_dhhi_demog.params[1]),str(reg_dma_product_fe_dhhi_demog.std_errors[1]),str(reg_dma_product_fe_dhhi_demog.pvalues[1]), \
			str(reg_dma_product_fe_dhhi_demog.params[2]),str(reg_dma_product_fe_dhhi_demog.std_errors[2]),str(reg_dma_product_fe_dhhi_demog.pvalues[2]), \
			str(reg_dma_product_fe_dhhi_demog.params[3]),str(reg_dma_product_fe_dhhi_demog.std_errors[3]),str(reg_dma_product_fe_dhhi_demog.pvalues[3]), \
			str(reg_dma_product_fe_dhhi_demog.nobs),str(reg_dma_product_fe_dhhi_demog.rsquared),'Yes','No']
		writer.writerow(res_dma_product_fe_dhhi_demog)

		# Product/market and time fixed effects, DHHI, demographics
		mod = PanelOLS(data['lprice'], data[['post_merger_dhhi','log_hhinc_per_person_adj']], entity_effects = True, time_effects = True)
		reg_time_fe_dhhi_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
		res_time_fe_dhhi_demog = ['Time FE, DHHI, Demographics','','','', \
			str(reg_time_fe_dhhi_demog.params[0]),str(reg_time_fe_dhhi_demog.std_errors[0]),str(reg_time_fe_dhhi_demog.pvalues[0]), \
			'','','','','','', \
			str(reg_time_fe_dhhi_demog.params[1]),str(reg_time_fe_dhhi_demog.std_errors[1]),str(reg_time_fe_dhhi_demog.pvalues[1]), \
			str(reg_time_fe_dhhi_demog.nobs),str(reg_time_fe_dhhi_demog.rsquared),'Yes','Yes']
		writer.writerow(res_time_fe_dhhi_demog)

		# Should we think about a case where we do a dummy for the second-largest firm too?

code = sys.argv[1]
log_out = open('../../../All/m_' + code + '/output/compute_did.log', 'w')
log_err = open('../../../All/m_' + code + '/output/compute_did.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = aux.parse_info(code)
merging_parties = aux.get_merging_parties(info_dict["MergingParties"])

for timetype in ['month', 'quarter']:
	df = pd.read_csv('../../../All/m_' + code + '/intermediate/data_' + timetype + '.csv', delimiter = ',')
	df = aux.append_owners(code, df, timetype)
	if timetype == 'month':
		write_overlap(code, df, info_dict["DateCompleted"], merging_parties)
	dt = datetime.strptime(info_dict["DateCompleted"], '%Y-%m-%d')
	did(df, dt, merging_parties, timetype)

log_out.close()
log_err.close()