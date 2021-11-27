'''
This script uses the datasets "stata_did_month.csv" created in the 5th
step of the process (compute_did.py) and the datasets "demand_month.csv"
created in the 9th step of the proces (compute_demand.py) in order to
create the final dataset "stata_did_int_month.csv" to be used in the
estimation of the final diff in diff routine.

It also updates the computation of hhi and dhhi to take into account
that store-brands ownership needs to be calculated at the chain level
and not at the dma_code level.
'''

import sys
import pandas as pd
import numpy as np
import unicodecsv as csv
import auxiliary as aux
from datetime import datetime
import subprocess
import os
import re


def parse_info(code):

	'''
	From the merger code we get all elements in the info.txt
	as a dictionary.
	'''

	file = open('../../../All/' + code + '/info.txt', mode = 'r')
	info_file = file.read()
	file.close()

	all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
	info_dict = {}
	for info in all_info_elements:
		info_name = info.group(1).strip()
		info_content = info.group(2).strip()
		info_dict[info_name] = info_content
	return info_dict


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


def add_dhhi(df, merging_date, month_or_quarter):

	# Pull merger year and merger month (or quarter)
	if month_or_quarter == 'month':
		merger_month_or_quarter = merging_date.month
	elif month_or_quarter == 'quarter':
		merger_month_or_quarter = np.ceil(merging_date.month/3)
	merger_year = merging_date.year

	# First, create shares for pre-merger period at the DMA level
	df_pre = df.loc[(df['year'] < merger_year) | ((df['year'] == merger_year) & (df[month_or_quarter] < merger_month_or_quarter))].copy()
	df_pre = df_pre.groupby(['upc','dma_code'])['shares','brand_code_uc'].agg({'shares':'sum','brand_code_uc':'first'}).reset_index()
	df_pre['dma_share'] = df_pre.groupby('dma_code')['shares'].transform('sum') # We may want to generalize this. Right now, it assumes that market size is constant over time.
	df_pre['inside_share'] = df_pre['shares']/df_pre['dma_share']
	df_pre = df_pre[['upc','dma_code','inside_share']]
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
	df_pre_own = aux.append_owners(code, df_pre, month_or_quarter, add_dhhi = True)

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

	df_post_own = aux.append_owners(code, df_post, month_or_quarter, add_dhhi = True)

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


def did(df, merging_date, merging_parties, major_competitor = None, month_or_quarter = 'month'):

	# Pull merger year and merger month (or quarter)
	if month_or_quarter == 'month':
		merger_month_or_quarter = merging_date.month
	elif month_or_quarter == 'quarter':
		merger_month_or_quarter = np.ceil(merging_date.month/3)
	merger_year = merging_date.year

	# Add DHHI, add DMA/UPC indicator, log price and post-merger indicator
	df = add_dhhi(df, merging_date, month_or_quarter)
	df['dma_upc'] = df['dma_code'].astype(str) + "_" + df['upc'].astype(str)
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
	df['trend'] = (df['year'] - min_year)*num_periods + df[month_or_quarter] - min_month_or_quarter

	df['time_index'] = df['year']*100 + df[month_or_quarter]
	data = df.set_index(['dma_upc', 'time_index'])

	# Add interaction terms
	data['post_merger_merging'] = data['post_merger']*data['merging']
	data['post_merger_dhhi'] = data['post_merger']*data['dhhi']

	if major_competitor is not None:
		data['major_competitor'] = data['owner'].isin(major_competitor)
		data['post_merger_major'] = data['post_merger']*data['major_competitor']

	# Add demographics
	data['log_hhinc_per_person_adj'] = np.log(data['hhinc_per_person'])

	# store dataset
	data.to_csv('../../../All/m_' + code + '/intermediate/stata_did_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8', index = False)


def run_did(code):

	info_dict = parse_info(code)
	year_c = info_dict['DateCompleted'][0:4]
	month_c = str(int(info_dict['DateCompleted'][5:7]))
	year_a = info_dict['DateAnnounced'][0:4]
	month_a = str(int(info_dict['DateAnnounced'][5:7]))

	dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/DiD_interactions2.do"
	DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"

	codes = ['1817013020_1', '1924129020_11', '1923401020_1', '2614332020_1', '2736521020_9']

	if code not in codes:

		path_output = "../output/"
		cmd = ([DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input,
	            path_output, month_or_quarter, year_c, month_c, year_a, month_a])
		subprocess.call(cmd)


def data_update(folder, base_folder, month_or_quarter='month'):

	code = folder
	m_folder = base_folder + code + "/output"
	path_input = base_folder + code + "/intermediate"

	info_dict = parse_info(code)
	year_c = info_dict['DateCompleted'][0:4]
	month_c = str(int(info_dict['DateCompleted'][5:7]))
	year_a = info_dict['DateAnnounced'][0:4]
	month_a = str(int(info_dict['DateAnnounced'][5:7]))

	#open the did data
	df = pd.read_csv(path_input + "/stata_did_month.csv", sep=",", index_col=['upc', 'dma_code', 'year', 'month'])
	print('open succesfull')
	# open demand data to get instruments
	inst = pd.read_csv(path_input + "/demand_month.csv", delimiter=',', index_col=['upc', 'dma_code', 'year', 'month'])
	print('open inst successfull')
	# keep only instrument columns (and index).
	demand_cols = [col for col in inst if col.startswith('demand')]
	inst = inst[demand_cols]

	# merge "stata_did_month.csv" with instrument columns from "demand_month.csv"
	df = pd.merge(df, inst, on=['upc', 'dma_code', 'year', 'month'], how='left')
	df.reset_index(inplace=True)
	print('merger sucessfull')
	print(df.columns)
	# merger with distance data
	df = df.set_index(['brand_code_uc', 'owner', 'dma_code', 'year', 'month'])
	dist = pd.read_csv(path_input + "/distances.csv", delimiter=',', index_col=['brand_code_uc', 'owner', 'dma_code', 'year', 'month'])

	df = df.merge(dist, on=['brand_code_uc', 'owner', 'dma_code', 'year', 'month'], how='left')

	df = df.reset_index()
	df.to_csv(path_input + '/stata_did_int_month.csv', sep=',', encoding='utf-8', index=False)


def load_store_table(year):

	'''
	foreach year load the stores file to see where the store_brand upcs
	where sold
	'''
	store_path = "../../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
	store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
	print("Loaded store file of "+ year)
	return store_table


def load_movement_table(year, group, module, path = ''):

	'''
	for each year/group/module load the movement files
	'''
	if path == '':
		path = "../../../Data/nielsen_extracts/RMS/" + year + "/Movement_Files/" + group + "_" + year + "/" + module + "_" + year + ".tsv"

	assert os.path.exists(path), "File does not exist: %r" % path

	table = pd.read_csv(path, delimiter = "\t")

	return table


def store_list(code, years, groups, modules, merger_start_date, merger_stop_date):

	# upc list has 'upc', 'owner'
	store_upcs = pd.read_csv('../../../All/' + code + '/properties/store_upcs.csv', sep = ',', encoding = 'utf-8')

	info_dict = parse_info(folder)

	stop_dt = datetime.strptime(merger_stop_date, '%Y-%m-%d')
	start_dt = datetime.strptime(merger_start_date, '%Y-%m-%d')
	stop_month_int = stop_dt.year * 12 + stop_dt.month
	start_month_int = start_dt.year * 12 + start_dt.month

	pre_months = 24
	post_months = 24
	min_year, min_month = aux.int_to_month(start_month_int - pre_months)
	max_year, max_month = aux.int_to_month(stop_month_int + post_months)

	if ((code=='m_1817013020_3') & (max_year > 2008)):
		max_year = 2008
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2008, years))

	#manual fix for bread
	if ((code=='m_2203820020_1') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for buns
	if ((code=='m_2203820020_2') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for rolls
	if ((code=='m_2203820020_3') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for pies
	if ((code=='m_2203820020_8') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for bakery remaining
	if ((code=='m_2203820020_10') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for cheesecake
	if ((code=='m_2203820020_11') & (max_year > 2012)):
		print('it entered the  if')
		max_year = 2012
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2012, years))
		print(years)

	#manual fix for biscuits
	if ((code=='m_2203820020_12') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		max_quarter = 4
		years = list(filter(lambda x: int(x) <= 2012, years))

		#manual fix for RBC_Bread
	if ((code=='m_2033113020_2') & (min_year < 2007)):
		min_year = 2007
		min_month = 1
		min_quarter = 1
		years = list(filter(lambda x: int(x) >= 2007, years))

		#manual fix for RBC_Cake
	if ((code=='2033113020_3') & (min_year < 2007)):
		min_year = 2007
		min_month = 1
		min_quarter = 1
		years = list(filter(lambda x: int(x) >= 2007, years))

		#manual fix for Headache pills
	if ((code=='2373087020_1') & (min_year < 2010)):
		min_year = 2010
		min_month = 1
		min_quarter = 1
		years = list(filter(lambda x: int(x) >= 2010, years))

		#manual fix for School and Office Supplies
	if ((code=='m_2363232020_4') & (min_year < 2010)):
		min_year = 2010
		min_month = 1
		min_quarter = 1
		years = list(filter(lambda x: int(x) >= 2010, years))

		#manual fix for RBC BREAD
	if ((code=='m_2495767020_14') & (min_year < 2012)):
		min_year = 2012
		min_month = 1
		min_quarter
		years = list(filter(lambda x: int(x) >= 2012, years))


	if len(store_upcs)!=0:
		df1 = pd.DataFrame()
		df2 = pd.DataFrame()

		for year in years:
			store_table = load_store_table(year)

			# df2 has 'store_code_uc', 'parent_code', 'dma_code'
			df2 = df2.append(store_table)

			for group, module in zip(groups, modules):
				print(group, module, year)
				movement_table = load_movement_table(year, group, module)
				movement_table['year'] = year
				movement_table['sales'] = movement_table['price'] * movement_table['units'] / movement_table['prmult']

				# df1 has 'upc', 'store_code_uc', year, and sales
				df1 = df1.append(movement_table.groupby(['upc', 'store_code_uc', 'year'])['sales'].agg(['sum']).reset_index())

		# all store upcs and their store_code_uc, year, and sales
		df1 = pd.merge(store_upcs, df1, on='upc', how='inner').reset_index()
		df1['year'] = df1['year'].astype(int)
		df1.rename(columns = {'sum': 'sales'}, inplace = True)
		print(df1.columns)

		# all unique combinations of store_code_uc, parent_code, dma_code, and year
		df2 = df2.groupby(['store_code_uc', 'parent_code', 'dma_code', 'year'])['year'].agg(['mean']).reset_index()
		df2['year'] = df2['year'].astype(int)
		print(df2.columns)

		# merge upc (store brands) and 'store_code_uc' with 'parent_code' and 'dma_code' data
		df1 = pd.merge(df1, df2, on=['store_code_uc', 'year'], how='inner')
		df1 = df1.drop(['index', 'mean_x', 'mean_y'], axis=1)
		#df1['tot_sales'] = df1.groupby(['parent_code', 'dma_code', 'year', 'upc'])['sales'].transform('sum')
		df1 = df1.drop_duplicates(['upc', 'parent_code', 'dma_code', 'year'])

		#now we keep the parent_code with largest sales for the year
		df1['largest_sales'] = df1.groupby(['upc', 'dma_code', 'year'])['sales'].transform('max')
		df1 = df1[df1['largest_sales']==df1['sales']]

		# save to csv
		df1.to_csv('../../../All/' + code + '/properties/store_codes.csv', sep = ',', encoding = 'utf-8')


def upc_list(code):

	'''
	Generate the list of store brand upcs that are present in the
	merger dataset. Store that list in properties/store_upcs.csv
	'''

	path_input = "../../../All/" + code + "/intermediate"
	data = pd.read_csv(path_input + "/stata_did_int_month.csv")

	# homogeneize store ownership names
	labels = ["multiple owners", "multiple", "Several owners", "Several Owners",
			  "several owners", "SEVERAL OWNERS", "Many owners", "MANY OWNERS",
			  "0", "Store Brands", "Store Brand", "VARIOUS OWNERS", "various owners",
			  "Ctl Br", "CTL BR", "Control Brands"]

	for label in labels:
		data.loc[data['owner']==label, "owner"] = "several owners"

	data.loc[data['brand_code_uc']==536746, "owner"] = "several owners"

	# keep only upcs with "several owners" as the owner and store that dataframe
	data = data[data['owner']=='several owners']
	data = data.groupby(['upc', 'owner'])['prices'].agg(['mean'])
	data.to_csv('../../../All/' + code + '/properties/store_upcs.csv', sep = ',', encoding = 'utf-8')


def merge(code):

	store_upcs = pd.read_csv('../../../All/' + code + '/properties/store_upcs.csv')

	if len(store_upcs)!=0:

		store_codes = pd.read_csv('../../../All/' + code + '/properties/store_codes.csv')
		store_codes = store_codes[['upc', 'dma_code', 'year', 'parent_code']]
		did_data = pd.read_csv('../../../All/' + code + '/intermediate/stata_did_int_month.csv')
		did_data = pd.merge(did_data, store_codes, on=['year', 'upc', 'dma_code'], how='left')
		did_data.to_csv('../../../All/' + code + '/intermediate/stata_did_int_month.csv')


def master_did(folder, base_folder, month_or_quarter='month'):

	data_update(folder, base_folder)
	upc_list(folder)
	info_dict = parse_info(folder)
	groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
	groups = [str(0) + str(group) if len(str(group)) == 3 else group for group in groups]
	years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])
	store_list(folder, years, groups, modules, info_dict["DateAnnounced"], info_dict["DateCompleted"])
	merge(folder)


log_out = open('output/master_did.log', 'w')
log_err = open('output/master_did.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

'''
The goal of the chunk of code below is to update everything that's necessary
by either (or both) updating the original diff in diff dataset (data_month.csv)
and then the updated diff in diff datasets stata_did_month.csv and stata_did_int_month.csv
and then run the actual diff in diff if wanted. The last step requires uncommenting the
line right below "master_did(folder, base_folder)" since that one calls "run_did(code)". If
the data was updated already, we can silence master_did(), however, this is a manual check,
there's no code to check whether everything is up-to-date.
'''

base_folder = '../../../All/'
folders = [folder for folder in os.listdir(base_folder)]

for folder in folders:

	if os.path.exists(base_folder + folder + '/intermediate/demand_month.csv'):

		if os.path.exists(base_folder + folder + '/intermediate/stata_did_month.csv'):

			print('ready to crunch ' + folder )
			# if both datasets exists let's update the datasets and do the data crunching
			#master_did(folder, base_folder)
			code = folder[2:]
			run_did(code)

		else:

			print('need to get original diff in diff ' + folder )
			#if the original did dataset does not exist, let's build it
			code = folder[2:]
			info_dict = aux.parse_info(code)
			merging_parties = aux.get_parties(info_dict["MergingParties"])

			for timetype in ['month', 'quarter']:
				df = pd.read_csv('../../../All/m_' + code + '/intermediate/data_' + timetype + '.csv', delimiter = ',')
				df = aux.append_owners(code, df, timetype)
				if timetype == 'month':
					overlap_df = write_overlap(code, df, info_dict["DateCompleted"], merging_parties)
					if "MajorCompetitor" in info_dict:
						major_competitor = aux.get_parties(info_dict["MajorCompetitor"])
					else:
						major_competitor = get_major_competitor(overlap_df)

				dt = datetime.strptime(info_dict["DateCompleted"], '%Y-%m-%d')
				did(df, dt, merging_parties, major_competitor = major_competitor, month_or_quarter = timetype)
				master_did(folder, base_folder)

