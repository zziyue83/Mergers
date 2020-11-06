import sys
import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import unicodecsv as csv
import auxiliary as aux
from datetime import datetime
from linearmodels.panel import compare
import subprocess

def append_aggregate_demographics(df, month_or_quarter):

	# Load agent data
	agent_data = pd.read_csv('../../../All/master/agent_data_' + month_or_quarter + '.csv', delimiter = ',')

	# Per-person income
	agent_data['hhinc_per_person'] = agent_data['HINCP_ADJ'] / agent_data['hhmember']

	# Compute mean demographics by DMA and month or quarter
	dma_stats = agent_data.groupby(['year','dma_code'])['hhinc_per_person'].agg('median').reset_index()

	# For data error with median HH income = 0, set median equal to prior year's
	dma_stats.loc[(dma_stats['dma_code']==528) & (dma_stats['year']==2014),'hhinc_per_person'] = dma_stats.loc[(dma_stats['dma_code']==528) & (dma_stats['year']==2013),'hhinc_per_person']
	demog_map = dma_stats.to_dict()

	# Map to main dataframe
	data_years = df['year'].unique()
	agent_years = df['year'].unique()
	for year in data_years:
		if year not in agent_years:
			raise Exception('demographics data do not span the whole dataset.')
	df = df.merge(dma_stats,left_on=['year','dma_code'],right_on=['year','dma_code'])

	return df

def compute_hhi_map(df, owner_col = 'owner'):

	# df should have dma, upc, owner, shares
	df = df[['dma_code', 'shares', owner_col]]
	df = df.groupby(['dma_code', owner_col]).sum()

	# Compute HHI
	df['shares2'] = df['shares'] * df['shares']
	df = df.groupby('dma_code').sum()
	df = df.rename(columns = {'shares2' : 'hhi'})
	df = df['hhi']
	hhi_map = df.to_dict()
	return hhi_map

def add_dhhi_brandlevel(df, merging_date, month_or_quarter, code):

	# Pull merger year and merger month (or quarter)
	if month_or_quarter == 'month':
		merger_month_or_quarter = merging_date.month
	elif month_or_quarter == 'quarter':
		merger_month_or_quarter = np.ceil(merging_date.month/3)
	merger_year = merging_date.year

	# First, create shares for pre-merger period at the DMA level
	df_pre = df.loc[(df['year'] < merger_year) | ((df['year'] == merger_year) & (df[month_or_quarter] < merger_month_or_quarter))].copy()
	df_pre = df_pre.groupby(['brand_code_uc','dma_code'])['shares'].agg({'shares':'sum'}).reset_index()
	df_pre['dma_share'] = df_pre.groupby('dma_code')['shares'].transform('sum') # We may want to generalize this. Right now, it assumes that market size is constant over time.
	df_pre['inside_share'] = df_pre['shares']/df_pre['dma_share']
	df_pre = df_pre[['brand_code_uc','dma_code','inside_share']]
	df_pre = df_pre.rename(columns = {'inside_share' : 'shares'})

	# Subtract 2 months/quarters for the "pre" just to deal with indexing issues
	if merger_month_or_quarter > 2:
		df_pre[month_or_quarter] = merger_month_or_quarter - 2
		df_pre['year'] = merger_year
	elif merger_month_or_quarter == 2:
		if month_or_quarter == 'month':
			df_pre[month_or_quarter] = 12
		elif month_or_quarter == 'quarter':
			df_pre[month_or_quarter] = 4
		df_pre['year'] = merger_year - 1
	elif merger_month_or_quarter == 1:
		if month_or_quarter == 'month':
			df_pre[month_or_quarter] = 11
		elif month_or_quarter == 'quarter':
			df_pre[month_or_quarter] = 3
		df_pre['year'] = merger_year - 1

	print(df_pre[[month_or_quarter, 'year']])
	df_pre_own = aux.append_owners_brandlevel(code, df_pre, month_or_quarter, add_dhhi = True)

	# Get inside HHI pre at the DMA level
	pre_hhi_map = compute_hhi_map(df_pre_own[['dma_code', 'shares', 'owner']])
	df['pre_hhi'] = df['dma_code'].map(pre_hhi_map)

	# Now, get owners post merger
	df_post = df_pre.copy()

	# Add 2 months/quarters for the "post" just to deal with indexing issues
	if month_or_quarter == 'month':
		if merger_month_or_quarter == 11:
			df_post['month'] = 1
			df_post['year'] = merger_year + 1
		elif merger_month_or_quarter == 12:
			df_post['month'] = 2
			df_post['year'] = merger_year + 1
		else:
			df_post['month'] = merger_month_or_quarter + 2
			df_post['year'] = merger_year
	elif month_or_quarter == 'quarter':
		if merger_month_or_quarter == 3:
			df_post['quarter'] = 1
			df_post['year'] = merger_year + 1
		elif merger_month_or_quarter == 4:
			df_post['quarter'] = 2
			df_post['year'] = merger_year + 1
		else:
			df_post['quarter'] = merger_month_or_quarter + 2
			df_post['year'] = merger_year
	print(df_post[[month_or_quarter, 'year']])

	# if month_or_quarter == 'month':
	# 	new_month = df_post['month'] + 2
	# 	df_post['year'] = df_post['year'] + (new_month/12).astype(int)
	# 	df_post['month'] = new_month%12
	# elif month_or_quarter == 'quarter':
	# 	new_quarter = df_post['quarter'] + 2
	# 	df_post['year'] = df_post['year'] + (new_quarter/4).astype(int)
	# 	df_post['quarter'] = new_quarter%4
	# df_post['year'] = merger_year
	# df_post[month_or_quarter] = merger_month_or_quarter


	df_post_own = aux.append_owners_brandlevel(code, df_post, month_or_quarter, add_dhhi = True)

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
	total_sales = ms.total_sales.sum()

	df['post_merger'] = 0
	df.loc[(df['year']>merger_year) | ((df['year']==merger_year) & (df[month_or_quarter]>=merger_month_or_quarter)),'post_merger'] = 1

	# Get a dataframe that is pre-sales, post-sales, pre-shares, post-shares for all merging parties
	rows_list = []
	for party in df.owner.unique():
		party_sales_pre = df.sales[(df['owner'] == party) & (df['post_merger'] == 0)].sum()
		party_sales_post = df.sales[(df['owner'] == party) & (df['post_merger'] == 1)].sum()
		party_sales = df.sales[df['owner'] == party].sum()
		party_share_pre = party_sales_pre / total_sales_pre
		party_share_post = party_sales_post / total_sales_post
		party_share = party_sales / total_sales

		if party in merging_parties:
			is_merging_party = 1
		else:
			is_merging_party = 0

		this_dict = {'name' : party, 'pre_sales' : party_sales_pre, 'post_sales' : party_sales_post, 'pre_share' : party_share_pre, 'post_share' : party_share_post, 'overall_share' : party_share, 'overall_sales' : party_sales, 'merging_party' : is_merging_party}
		rows_list.append(this_dict)
	overlap_df = pd.DataFrame(rows_list)
	overlap_df = overlap_df.sort_values(by = 'merging_party', ascending = False)
	overlap_df.to_csv('../../../All/m_' + code + '/output/overlap.csv', sep = ',', encoding = 'utf-8', index = False)
	return overlap_df

def get_major_competitor(df, ownership_groups = None):
	df = df[df.merging_party == 0]
	if ownership_groups is None:
		where_max = df.overall_sales.idxmax()
		major_competitor = [df.name[where_max]]
	print(major_competitor)
	return major_competitor

def did_brandlevel(df, merging_date, merging_parties, major_competitor = None, month_or_quarter = 'month', code):

	# Pull merger year and merger month (or quarter)
	if month_or_quarter == 'month':
		merger_month_or_quarter = merging_date.month
	elif month_or_quarter == 'quarter':
		merger_month_or_quarter = np.ceil(merging_date.month/3)
	merger_year = merging_date.year

	# Add DHHI, add DMA/UPC indicator, log price and post-merger indicator
	df = add_dhhi_brandlevel(df, merging_date, month_or_quarter)
	df['dma_brand'] = df['dma_code'].astype(str) + "_" + df['brand_code_uc'].astype(str)
	df['lprice'] = np.log(df['prices'])
	df['post_merger'] = 0
	df.loc[(df['year']>merger_year) | ((df['year']==merger_year) & (df[month_or_quarter]>=merger_month_or_quarter)),'post_merger'] = 1
	df['merging'] = df['owner'].isin(merging_parties)


	# Append demographics and adjust for inflation
	df = append_aggregate_demographics(df, month_or_quarter)
	df = aux.adjust_inflation(df, ['hhinc_per_person'], month_or_quarter)
	min_year = df['year'].min()
	temp = df[df['year'] == min_year]
	min_month_or_quarter = temp[month_or_quarter].min()
	if month_or_quarter == 'month':
		num_periods = 12
	else:
		num_periods = 4
	# df['trend'] = 0
	df['trend'] = (df['year'] - min_year)*num_periods + df[month_or_quarter] - min_month_or_quarter
	# df.loc[df['year'] == min_year]['trend'] = df.loc[df['year'] == min_year][month_or_quarter] - min_month_or_quarter
	# df.loc[df['year'] > min_year]['trend'] = (num_periods - min_month_or_quarter) + num_periods * (df.loc[df['year'] > min_year]['year'] - min_year - 1) + df[df['year'] > min_year][month_or_quarter]

	df['time_index'] = df['year']*100 + df[month_or_quarter]
	data = df.set_index(['dma_brand', 'time_index'])

	# Add interaction terms
	data['post_merger_merging'] = data['post_merger']*data['merging']
	data['post_merger_dhhi'] = data['post_merger']*data['dhhi']

	if major_competitor is not None:
		data['major_competitor'] = data['owner'].isin(major_competitor)
		data['post_merger_major'] = data['post_merger']*data['major_competitor']


	# Add demographics
	data['log_hhinc_per_person_adj'] = np.log(data['hhinc_per_person'])

	use_stata = True
	if use_stata:
		data.to_csv('../../../All/m_' + code + '/intermediate/stata_did_' + month_or_quarter + '_brandlevel.csv', sep = ',', encoding = 'utf-8', index = False)

		dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Main/did_test2_brandlevel.do"
		DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
		path_input = "../../../All/m_" + code + "/intermediate"
		path_output = "../output/"
		cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, month_or_quarter]

		subprocess.call(cmd)

		estimate_type = ['0', '1', '2', '3']

		for est_type in estimate_type:

			read_file = pd.read_csv(path_input + "/"+ path_output + "brandlevel_did_stata_" + month_or_quarter + '_' + est_type + ".txt", sep = "\t")
			read_file = read_file.replace(np.nan, '', regex=True)
			read_file.to_csv(path_input + "/" + path_output + "brandlevel_did_stata_" + month_or_quarter + '_' + est_type + ".csv", index=None)



	else:
		with open('../../../All/m_' + code + '/output/did_' + month_or_quarter + '.csv', "wb") as csvfile:
			header = ["model","post_merger*merging", "post_merger*merging_se", "post_merger*merging_pval", \
			          "post_merger*dhhi", "post_merger*dhhi_se", "post_merger*dhhi_pval", "post_merger", \
			          "post_merger_se", "post_merger_pval", "post_merger*major", "post_merger*major_se", "post_merger*major_pval", \
			          "trend", "trend_se", "trend_pval", "log_hhinc_per_person_adj", "log_hhinc_per_person_adj_se", "log_hhinc_per_person_adj_pval", "N", "r2", "product", "time"]
			writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
			writer.writerow(header)

			# Run the various regressions

			# No fixed effects
			exog_vars = ['post_merger_merging', 'post_merger', 'trend']
			exog = sm.add_constant(data[exog_vars])
			mod = PanelOLS(data['lprice'], exog, entity_effects = False, time_effects = False)
			reg_nofe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_nofe_csv = ['No FE',str(reg_nofe.params[1]),str(reg_nofe.std_errors[1]), str(reg_nofe.pvalues[1]), \
				'','','', \
				str(reg_nofe.params[2]),str(reg_nofe.std_errors[2]),str(reg_nofe.pvalues[2]), '', '', '', \
				str(reg_nofe.params[3]),str(reg_nofe.std_errors[3]),str(reg_nofe.pvalues[3]), \
				'','','', \
				str(reg_nofe.nobs),str(reg_nofe.rsquared),'No','No']
			writer.writerow(res_nofe_csv)

			# Product/market fixed effects
			mod = PanelOLS(data['lprice'], data[exog_vars], entity_effects = True, time_effects = False)
			reg_dma_product_fe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_dma_product_fe_csv = ['DMA/Product FE',str(reg_dma_product_fe.params[0]),str(reg_dma_product_fe.std_errors[0]),str(reg_dma_product_fe.pvalues[0]), \
				'','','', \
				str(reg_dma_product_fe.params[1]),str(reg_dma_product_fe.std_errors[1]),str(reg_dma_product_fe.pvalues[1]), '','','', \
				str(reg_dma_product_fe.params[2]),str(reg_dma_product_fe.std_errors[2]),str(reg_dma_product_fe.pvalues[2]), \
				'','','', \
				str(reg_dma_product_fe.nobs),str(reg_dma_product_fe.rsquared),'Yes','No']
			writer.writerow(res_dma_product_fe_csv)

			# Product/market and time fixed effects
			mod = PanelOLS(data['lprice'], data['post_merger_merging'], entity_effects = True, time_effects = True)
			reg_time_fe = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_time_fe_csv = ['Time FE',str(reg_time_fe.params[0]),str(reg_time_fe.std_errors[0]),str(reg_time_fe.pvalues[0]), \
				'','','','','','','','','','','','', '', '', '',\
				str(reg_time_fe.nobs),str(reg_time_fe.rsquared),'Yes','Yes']
			writer.writerow(res_time_fe_csv)

			# No fixed effects, but with major
			exog_vars = ['post_merger_merging', 'post_merger', 'post_merger_major', 'trend']
			exog = sm.add_constant(data[exog_vars])
			mod = PanelOLS(data['lprice'], exog, entity_effects = False, time_effects = False)
			reg_nofe_major = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_nofe_major_csv = ['No FE, Major',str(reg_nofe_major.params[1]),str(reg_nofe_major.std_errors[1]), str(reg_nofe_major.pvalues[1]), \
				'','','', \
				str(reg_nofe_major.params[2]),str(reg_nofe_major.std_errors[2]),str(reg_nofe_major.pvalues[2]), \
				str(reg_nofe_major.params[3]),str(reg_nofe_major.std_errors[3]),str(reg_nofe_major.pvalues[3]), \
				str(reg_nofe_major.params[4]),str(reg_nofe_major.std_errors[4]),str(reg_nofe_major.pvalues[4]), \
				'','','', \
				str(reg_nofe_major.nobs),str(reg_nofe_major.rsquared),'No','No']
			writer.writerow(res_nofe_major_csv)

			# Product/market fixed effects
			mod = PanelOLS(data['lprice'], data[exog_vars], entity_effects = True, time_effects = False)
			reg_dma_product_fe_major = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_dma_product_fe_major_csv = ['DMA/Product FE, Major',str(reg_dma_product_fe_major.params[0]),str(reg_dma_product_fe_major.std_errors[0]),str(reg_dma_product_fe_major.pvalues[0]), \
				'','','', \
				str(reg_dma_product_fe_major.params[1]),str(reg_dma_product_fe_major.std_errors[1]),str(reg_dma_product_fe_major.pvalues[1]), \
				str(reg_dma_product_fe_major.params[2]),str(reg_dma_product_fe_major.std_errors[2]),str(reg_dma_product_fe_major.pvalues[2]), \
				str(reg_dma_product_fe_major.params[3]),str(reg_dma_product_fe_major.std_errors[3]),str(reg_dma_product_fe_major.pvalues[3]), \
				'','','', \
				str(reg_dma_product_fe_major.nobs),str(reg_dma_product_fe_major.rsquared),'Yes','No']
			writer.writerow(res_dma_product_fe_major_csv)

			# Product/market and time fixed effects
			mod = PanelOLS(data['lprice'], data[['post_merger_merging', 'post_merger_major']], entity_effects = True, time_effects = True)
			reg_time_fe_major = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_time_fe_major_csv = ['Time FE, Major',str(reg_time_fe_major.params[0]),str(reg_time_fe_major.std_errors[0]),str(reg_time_fe_major.pvalues[0]), \
				'','','','','','',
				str(reg_time_fe_major.params[1]),str(reg_time_fe_major.std_errors[1]),str(reg_time_fe_major.pvalues[1]),
				'','','','','','', \
				str(reg_time_fe_major.nobs),str(reg_time_fe_major.rsquared),'Yes','Yes']
			writer.writerow(res_time_fe_major_csv)

			# No fixed effects, DHHI
			exog_vars_dhhi = ['post_merger_dhhi', 'post_merger', 'trend']
			exog_dhhi = sm.add_constant(data[exog_vars_dhhi])
			mod = PanelOLS(data['lprice'], exog_dhhi, entity_effects = False, time_effects = False)
			reg_nofe_dhhi = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_nofe_dhhi_csv = ['No FE, DHHI','','','', \
				str(reg_nofe_dhhi.params[1]),str(reg_nofe_dhhi.std_errors[1]),str(reg_nofe_dhhi.pvalues[1]), \
				str(reg_nofe_dhhi.params[2]),str(reg_nofe_dhhi.std_errors[2]),str(reg_nofe_dhhi.pvalues[2]), '', '', '', \
				str(reg_nofe_dhhi.params[3]),str(reg_nofe_dhhi.std_errors[3]),str(reg_nofe_dhhi.pvalues[3]), \
				'','','', \
				str(reg_nofe_dhhi.nobs),str(reg_nofe_dhhi.rsquared),'No','No']
			writer.writerow(res_nofe_dhhi_csv)

			# Product/market fixed effects, DHHI
			mod = PanelOLS(data['lprice'], data[exog_vars_dhhi], entity_effects = True, time_effects = False)
			reg_dma_product_fe_dhhi = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_dma_product_fe_dhhi_csv = ['DMA/Product FE, DHHI','','','', \
				str(reg_dma_product_fe_dhhi.params[0]),str(reg_dma_product_fe_dhhi.std_errors[0]),str(reg_dma_product_fe_dhhi.pvalues[0]), \
				str(reg_dma_product_fe_dhhi.params[1]),str(reg_dma_product_fe_dhhi.std_errors[1]),str(reg_dma_product_fe_dhhi.pvalues[1]), '','','', \
				str(reg_dma_product_fe_dhhi.params[2]),str(reg_dma_product_fe_dhhi.std_errors[2]),str(reg_dma_product_fe_dhhi.pvalues[2]), \
				'','','', \
				str(reg_dma_product_fe_dhhi.nobs),str(reg_dma_product_fe_dhhi.rsquared),'Yes','No']
			writer.writerow(res_dma_product_fe_dhhi_csv)

			# Product/market and time fixed effects, DHHI
			mod = PanelOLS(data['lprice'], data['post_merger_dhhi'], entity_effects = True, time_effects = True)
			reg_time_fe_dhhi = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_time_fe_dhhi_csv = ['Time FE, DHHI','','','', \
				str(reg_time_fe_dhhi.params[0]),str(reg_time_fe_dhhi.std_errors[0]),str(reg_time_fe_dhhi.pvalues[0]), \
				'','','','','','','','','', '','','',\
				str(reg_time_fe_dhhi.nobs),str(reg_time_fe_dhhi.rsquared),'Yes','Yes']
			writer.writerow(res_time_fe_dhhi_csv)

			# No fixed effects, demographics
			exog_vars = ['post_merger_merging', 'post_merger', 'trend', 'log_hhinc_per_person_adj']
			exog = sm.add_constant(data[exog_vars])
			mod = PanelOLS(data['lprice'], exog, entity_effects = False, time_effects = False)
			reg_nofe_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_nofe_demog_csv = ['No FE, Demographics',str(reg_nofe_demog.params[1]),str(reg_nofe_demog.std_errors[1]),str(reg_nofe_demog.pvalues[1]), \
				'','','', \
				str(reg_nofe_demog.params[2]),str(reg_nofe_demog.std_errors[2]),str(reg_nofe_demog.pvalues[2]), '','','', \
				str(reg_nofe_demog.params[3]),str(reg_nofe_demog.std_errors[3]),str(reg_nofe_demog.pvalues[3]), \
				str(reg_nofe_demog.params[4]),str(reg_nofe_demog.std_errors[4]),str(reg_nofe_demog.pvalues[4]), \
				str(reg_nofe_demog.nobs),str(reg_nofe_demog.rsquared),'No','No']
			writer.writerow(res_nofe_demog_csv)

			# Product/market fixed effects, demographics
			mod = PanelOLS(data['lprice'], data[exog_vars], entity_effects = True, time_effects = False)
			reg_dma_product_fe_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_dma_product_fe_demog_csv = ['DMA/Product FE, Demographics',str(reg_dma_product_fe_demog.params[0]),str(reg_dma_product_fe_demog.std_errors[0]),str(reg_dma_product_fe_demog.pvalues[0]), \
				'','','', \
				str(reg_dma_product_fe_demog.params[1]),str(reg_dma_product_fe_demog.std_errors[1]),str(reg_dma_product_fe_demog.pvalues[1]), '','','', \
				str(reg_dma_product_fe_demog.params[2]),str(reg_dma_product_fe_demog.std_errors[2]),str(reg_dma_product_fe_demog.pvalues[2]), \
				str(reg_dma_product_fe_demog.params[3]),str(reg_dma_product_fe_demog.std_errors[3]),str(reg_dma_product_fe_demog.pvalues[3]), \
				str(reg_dma_product_fe_demog.nobs),str(reg_dma_product_fe_demog.rsquared),'Yes','No']
			writer.writerow(res_dma_product_fe_demog_csv)

			# Product/market and time fixed effects, demographics
			mod = PanelOLS(data['lprice'], data[['post_merger_merging','log_hhinc_per_person_adj']], entity_effects = True, time_effects = True)
			reg_time_fe_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_time_fe_demog_csv = ['Time FE, Demographics',str(reg_time_fe_demog.params[0]),str(reg_time_fe_demog.std_errors[0]),str(reg_time_fe_demog.pvalues[0]), \
				'','','','','','','','','', '','','',\
				str(reg_time_fe_demog.params[1]),str(reg_time_fe_demog.std_errors[1]),str(reg_time_fe_demog.pvalues[1]), \
				str(reg_time_fe_demog.nobs),str(reg_time_fe_demog.rsquared),'Yes','Yes']
			writer.writerow(res_time_fe_demog_csv)

			# No fixed effects, demographics, but with major
			exog_vars = ['post_merger_merging', 'post_merger', 'post_merger_major', 'trend', 'log_hhinc_per_person_adj']
			exog = sm.add_constant(data[exog_vars])
			mod = PanelOLS(data['lprice'], exog, entity_effects = False, time_effects = False)
			reg_nofe_demog_major = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_nofe_demog_major_csv = ['No FE, Major, Demographics',str(reg_nofe_demog_major.params[1]),str(reg_nofe_demog_major.std_errors[1]),str(reg_nofe_demog_major.pvalues[1]), \
				'','','', \
				str(reg_nofe_demog_major.params[2]),str(reg_nofe_demog_major.std_errors[2]),str(reg_nofe_demog_major.pvalues[2]),\
				str(reg_nofe_demog_major.params[3]),str(reg_nofe_demog_major.std_errors[3]),str(reg_nofe_demog_major.pvalues[3]), \
				str(reg_nofe_demog_major.params[4]),str(reg_nofe_demog_major.std_errors[4]),str(reg_nofe_demog_major.pvalues[4]), \
				str(reg_nofe_demog_major.params[5]),str(reg_nofe_demog_major.std_errors[5]),str(reg_nofe_demog_major.pvalues[5]), \
				str(reg_nofe_demog_major.nobs),str(reg_nofe_demog_major.rsquared),'No','No']
			writer.writerow(res_nofe_demog_major_csv)

			# Product/market fixed effects, demographics
			mod = PanelOLS(data['lprice'], data[exog_vars], entity_effects = True, time_effects = False)
			reg_dma_product_fe_demog_major = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_dma_product_fe_demog_major_csv = ['DMA/Product FE, Major, Demographics',str(reg_dma_product_fe_demog_major.params[0]),str(reg_dma_product_fe_demog_major.std_errors[0]),str(reg_dma_product_fe_demog.pvalues[0]), \
				'','','', \
				str(reg_dma_product_fe_demog_major.params[1]),str(reg_dma_product_fe_demog_major.std_errors[1]),str(reg_dma_product_fe_demog_major.pvalues[1]), \
				str(reg_dma_product_fe_demog_major.params[2]),str(reg_dma_product_fe_demog_major.std_errors[2]),str(reg_dma_product_fe_demog_major.pvalues[2]), \
				str(reg_dma_product_fe_demog_major.params[3]),str(reg_dma_product_fe_demog_major.std_errors[3]),str(reg_dma_product_fe_demog_major.pvalues[3]), \
				str(reg_dma_product_fe_demog_major.params[4]),str(reg_dma_product_fe_demog_major.std_errors[4]),str(reg_dma_product_fe_demog_major.pvalues[4]), \
				str(reg_dma_product_fe_demog_major.nobs),str(reg_dma_product_fe_demog_major.rsquared),'Yes','No']
			writer.writerow(res_dma_product_fe_demog_major_csv)

			# Product/market and time fixed effects, demographics
			mod = PanelOLS(data['lprice'], data[['post_merger_merging','post_merger_major','log_hhinc_per_person_adj']], entity_effects = True, time_effects = True)
			reg_time_fe_demog_major = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_time_fe_demog_major_csv = ['Time FE, Major, Demographics',str(reg_time_fe_demog_major.params[0]),str(reg_time_fe_demog_major.std_errors[0]),str(reg_time_fe_demog_major.pvalues[0]), \
				'','','','','','', \
				str(reg_time_fe_demog_major.params[1]),str(reg_time_fe_demog_major.std_errors[1]),str(reg_time_fe_demog_major.pvalues[1]), \
				'','','',\
				str(reg_time_fe_demog_major.params[2]),str(reg_time_fe_demog_major.std_errors[2]),str(reg_time_fe_demog_major.pvalues[2]), \
				str(reg_time_fe_demog_major.nobs),str(reg_time_fe_demog_major.rsquared),'Yes','Yes']
			writer.writerow(res_time_fe_demog_major_csv)

			# No fixed effects, DHHI, demographics
			exog_vars_dhhi = ['post_merger_dhhi', 'post_merger', 'trend', 'log_hhinc_per_person_adj']
			exog_dhhi = sm.add_constant(data[exog_vars_dhhi])
			mod = PanelOLS(data['lprice'], exog_dhhi, entity_effects = False, time_effects = False)
			reg_nofe_dhhi_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_nofe_dhhi_demog_csv = ['No FE, DHHI, Demographics','','','', \
				str(reg_nofe_dhhi_demog.params[1]),str(reg_nofe_dhhi_demog.std_errors[1]),str(reg_nofe_dhhi_demog.pvalues[1]), \
				str(reg_nofe_dhhi_demog.params[2]),str(reg_nofe_dhhi_demog.std_errors[2]),str(reg_nofe_dhhi_demog.pvalues[2]), '','','',\
				str(reg_nofe_dhhi_demog.params[3]),str(reg_nofe_dhhi_demog.std_errors[3]),str(reg_nofe_dhhi_demog.pvalues[3]), \
				str(reg_nofe_dhhi_demog.params[4]),str(reg_nofe_dhhi_demog.std_errors[4]),str(reg_nofe_dhhi_demog.pvalues[4]), \
				str(reg_nofe_dhhi_demog.nobs),str(reg_nofe_dhhi_demog.rsquared),'No','No']
			writer.writerow(res_nofe_dhhi_demog_csv)

			# Product/market fixed effects, DHHI, demographics
			mod = PanelOLS(data['lprice'], data[exog_vars_dhhi], entity_effects = True, time_effects = False)
			reg_dma_product_fe_dhhi_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_dma_product_fe_dhhi_demog_csv = ['DMA/Product FE, DHHI, Demographics','','','', \
				str(reg_dma_product_fe_dhhi_demog.params[0]),str(reg_dma_product_fe_dhhi_demog.std_errors[0]),str(reg_dma_product_fe_dhhi_demog.pvalues[0]), \
				str(reg_dma_product_fe_dhhi_demog.params[1]),str(reg_dma_product_fe_dhhi_demog.std_errors[1]),str(reg_dma_product_fe_dhhi_demog.pvalues[1]), '','','', \
				str(reg_dma_product_fe_dhhi_demog.params[2]),str(reg_dma_product_fe_dhhi_demog.std_errors[2]),str(reg_dma_product_fe_dhhi_demog.pvalues[2]), \
				str(reg_dma_product_fe_dhhi_demog.params[3]),str(reg_dma_product_fe_dhhi_demog.std_errors[3]),str(reg_dma_product_fe_dhhi_demog.pvalues[3]), \
				str(reg_dma_product_fe_dhhi_demog.nobs),str(reg_dma_product_fe_dhhi_demog.rsquared),'Yes','No']
			writer.writerow(res_dma_product_fe_dhhi_demog_csv)

			# Product/market and time fixed effects, DHHI, demographics
			mod = PanelOLS(data['lprice'], data[['post_merger_dhhi','log_hhinc_per_person_adj']], entity_effects = True, time_effects = True)
			reg_time_fe_dhhi_demog = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
			res_time_fe_dhhi_demog_csv = ['Time FE, DHHI, Demographics','','','', \
				str(reg_time_fe_dhhi_demog.params[0]),str(reg_time_fe_dhhi_demog.std_errors[0]),str(reg_time_fe_dhhi_demog.pvalues[0]), \
				'','','','','','', '','','', \
				str(reg_time_fe_dhhi_demog.params[1]),str(reg_time_fe_dhhi_demog.std_errors[1]),str(reg_time_fe_dhhi_demog.pvalues[1]), \
				str(reg_time_fe_dhhi_demog.nobs),str(reg_time_fe_dhhi_demog.rsquared),'Yes','Yes']
			writer.writerow(res_time_fe_dhhi_demog_csv)

			print(compare({'NoFE' : reg_nofe, 'P-D' : reg_dma_product_fe, 'P-D, T' : reg_time_fe, 'NoFE, HHI' : reg_nofe_dhhi, 'P-D, HHI' : reg_dma_product_fe_dhhi, 'P-D, T, HHI' : reg_time_fe_dhhi}))
			print(compare({'NoFE' : reg_nofe_demog, 'P-D' : reg_dma_product_fe_demog, 'P-D, T' : reg_time_fe_demog, 'NoFE, HHI' : reg_nofe_dhhi_demog, 'P-D, HHI' : reg_dma_product_fe_dhhi_demog, 'P-D, T, HHI' : reg_time_fe_dhhi_demog}))
			print(compare({'NoFE' : reg_nofe_major, 'P-D' : reg_dma_product_fe_major, 'P-D, T' : reg_time_fe_major, 'NoFE, Demo' : reg_nofe_demog_major, 'P-D, Demo' : reg_dma_product_fe_demog_major, 'P-D, T, Demo' : reg_time_fe_demog_major}))

if __name__ == "__main__": 
	code = sys.argv[1]
	log_out = open('../../../All/m_' + code + '/output/compute_did_brandlevel.log', 'w')
	log_err = open('../../../All/m_' + code + '/output/compute_did_brandlevel.err', 'w')
	sys.stdout = log_out
	sys.stderr = log_err

	info_dict = aux.parse_info(code)
	merging_parties = aux.get_parties(info_dict["MergingParties"])

	for timetype in ['month', 'quarter']:
		df = pd.read_csv('../../../All/m_' + code + '/intermediate/data_' + timetype + '_brandlevel'+'.csv', delimiter = ',')
		df = aux.append_owners_brandlevel(code, df, timetype)
		if timetype == 'month':
			overlap_df = write_overlap(code, df, info_dict["DateCompleted"], merging_parties)
			if "MajorCompetitor" in info_dict:
				major_competitor = aux.get_parties(info_dict["MajorCompetitor"])
				print("Getting major competitor from info.txt")
			else:
				major_competitor = get_major_competitor(overlap_df)
				print("Getting major competitor from shares")
			print(major_competitor)

		dt = datetime.strptime(info_dict["DateCompleted"], '%Y-%m-%d')
		did_brandlevel(df, dt, merging_parties, major_competitor = major_competitor, month_or_quarter = timetype, code = code)

	print("compute_did successfully terminated")
	log_out.close()
	log_err.close()
