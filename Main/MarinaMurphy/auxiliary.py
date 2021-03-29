import re
import sys
from datetime import datetime
import pyblp
import pickle
import pandas as pd
import numpy as np
import pandasql as ps
import os
import tqdm 

def parse_info(code):
	file = open('../../../../All/m_' + code + '/info.txt', mode = 'r')
	info_file = file.read()
	file.close()

	all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
	info_dict = {}
	for info in all_info_elements:
		info_name = info.group(1).strip()
		info_content = info.group(2).strip()
		info_dict[info_name] = info_content
	return info_dict

def get_insts_or_chars_or_nests(full_string):
	if ', ' in full_string:
		info_list = full_string.split(', ')
	elif ',' in full_string:
		info_list = full_string.split(',')
	else:
		info_list = [full_string]
	return info_list

def get_groups_and_modules(full_string):
	all_group_module = re.finditer('{(.*?),(.*?)}', full_string, re.DOTALL)
	groups = []
	modules = []
	for pair in all_group_module:
		groups.append(pair.group(1).strip())
		modules.append(pair.group(2).strip())
	return groups, modules

def int_to_month(value):
	year = np.floor((value - 1) / 12)
	month = value - 12 * year
	return year, month

def get_years(initial_year_string, final_year_string, pre_months = 24, post_months = 24):
	initial_dt = datetime.strptime(initial_year_string, '%Y-%m-%d')
	final_dt = datetime.strptime(final_year_string, '%Y-%m-%d')
	initial_month_int = initial_dt.year * 12 + initial_dt.month
	final_month_int = final_dt.year * 12 + final_dt.month
	min_year, min_month = int_to_month(initial_month_int - pre_months)
	max_year, max_month = int_to_month(final_month_int + post_months)

	years = []
	for i in range(int(min_year), int(max_year) + 1, 1):
		this_year = i
		if this_year >= 2006 and this_year <= 2018:
			years.append(str(this_year))
	return years

def get_parties(info_str):
	all_parties = re.finditer('{(.*?)}', info_str, re.DOTALL)
	merging_parties = []
	for i in all_parties:
		merging_parties.append(i.group(1).strip())
	return merging_parties

def load_chunked_year_module_movement_table(year, group, module, path = ''):
	if path == '':
		path = "../../../../Data/nielsen_extracts/RMS/" + year + "/Movement_Files/" + group + "_" + year + "/" + module + "_" + year + ".tsv"
	assert os.path.exists(path), "File does not exist: %r" % path
	table = pd.read_csv(path, delimiter = "\t", chunksize = 10000000)
	return table

def get_upc_ver_uc_map(year):
	upc_ver_path = "../../../../Data/nielsen_extracts/RMS/"+str(year)+"/Annual_Files/rms_versions_"+str(year)+".tsv"
	upc_vers = pd.read_csv(upc_ver_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = "upc")
	upc_vers = upc_vers['upc_ver_uc']
	upc_ver_map = upc_vers.to_dict()
	return upc_ver_map

def get_product_map(groups):
	products_path = "../../../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
	products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = ["upc","upc_ver_uc"])
	int_groups = [int(i) for i in groups]
	wanted_products = products[products['product_group_code'].isin(int_groups)]
	product_map = wanted_products
	return product_map

#Example:
# upc                                   15000004
# upc_ver_uc                                   1
# upc_descr               SIERRA NEVADA W BR NRB
# product_module_code                       5000
# product_module_descr                      BEER
# product_group_code                        5001
# product_group_descr                       BEER
# department_code                              8
# department_descr           ALCOHOLIC BEVERAGES
# brand_code_uc                           637860
# brand_descr                SIERRA NEVADA WHEAT
# multi                                        1
# size1_code_uc                            32992
# size1_amount                                12
# size1_units                                 OZ
# dataset_found_uc                           ALL
# size1_change_flag_uc                         0

def append_owners(code, df, month_or_quarter,add_dhhi = False):
	# Load list of UPCs and brands
	upcs = pd.read_csv('../../../../All/m_' + code + '/intermediate/upcs.csv', delimiter = ',', index_col = 'upc')
	upcs = upcs['brand_code_uc']
	upc_map = upcs.to_dict()

	# Map brands to dataframe (by UPC)
	df['brand_code_uc'] = df['upc'].map(upc_map)

	# Load ownership assignments
	brand_to_owner = pd.read_csv('../../../../All/m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')

	# Assign min/max year and month when listed as zero in ownership mapping
	min_year = df['year'].min()
	max_year = df['year'].max()

	if month_or_quarter == 'month':
		min_month = df.loc[df['year']==min_year,'month'].min()
		max_month = df.loc[df['year']==max_year,'month'].max()
	elif month_or_quarter == 'quarter':
		min_month = (3*(df.loc[df['year']==min_year,'quarter']-1)+1).min()
		max_month = (3*df.loc[df['year']==max_year,'quarter']).max()

	# Remove Onwership that starts later than the latest time in the dataframe
	brand_to_owner = brand_to_owner[(brand_to_owner['start_year'] < max_year) | ((brand_to_owner['start_year'] == max_year)&(brand_to_owner['start_month'] <= max_month))]
	# Remove Onwership that ends earlier than the earliest time in the dataframe
	brand_to_owner = brand_to_owner[(brand_to_owner['end_year'] > min_year) | ((brand_to_owner['end_year'] == min_year)&(brand_to_owner['end_month'] >= min_month)) | (brand_to_owner['end_year'] == 0)]

	brand_to_owner.loc[(brand_to_owner['start_month']==0) | (brand_to_owner['start_year']<min_year) | ((brand_to_owner['start_year']==min_year)&(brand_to_owner['start_month']<min_month)),'start_month'] = min_month
	brand_to_owner.loc[(brand_to_owner['start_year']==0) | (brand_to_owner['start_year']<min_year),'start_year'] = min_year
	brand_to_owner.loc[(brand_to_owner['end_month']==0) | (brand_to_owner['end_year']>max_year) | ((brand_to_owner['end_year']==max_year)&(brand_to_owner['end_month']>max_month)),'end_month'] = max_month
	brand_to_owner.loc[(brand_to_owner['end_year']==0) | (brand_to_owner['end_year']>max_year),'end_year'] = max_year

	# Throw error if (1) dates don't span the entirety of the sample period or
	# (2) ownership dates overlap
	brand_to_owner_test = brand_to_owner.copy()
	brand_to_owner_test = brand_to_owner_test.sort_values(by=['brand_code_uc', 'start_year', 'start_month'])

	if month_or_quarter == 'month':
		min_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).min()
		max_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).max()
		brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
		brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))
	elif month_or_quarter == 'quarter':
		min_date = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1)).min()
		max_date = pd.to_datetime(dict(year=df.year, month=3*df.quarter, day=1)).max()
		brand_to_owner_test.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner_test['start_month']/3)-1)+1
		brand_to_owner_test.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, brand_to_owner_test.end_year, brand_to_owner_test.end_year - 1)
		brand_to_owner_test.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, 3*(np.floor(brand_to_owner_test.end_month/3)), 12)
		brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
		brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))

	brand_dates = brand_to_owner_test.groupby('brand_code_uc')[['start_date_test', 'end_date_test']].agg(['min', 'max'])
	if ((brand_dates.start_date_test['min']!=min_date).sum() + (brand_dates.end_date_test['max']!=max_date).sum() > 0):
		print('Ownership definitions does not span the entire sample period:')
		for index, row in brand_dates.iterrows():
			if row.start_date_test['min'] != min_date or row.end_date_test['max'] != max_date:
				print(index)
				print('start_date: ', row.start_date_test['min'])
				print('end_date: ', row.end_date_test['max'])

	brand_to_owner_test['owner_num'] = brand_to_owner_test.groupby('brand_code_uc').cumcount()+1
	max_num_owner = brand_to_owner_test['owner_num'].max()
	brand_to_owner_test = brand_to_owner_test.set_index('owner_num',append=True)
	brand_to_owner_test = brand_to_owner_test.unstack('owner_num')
	brand_to_owner_test.columns = ['{}_{}'.format(var, num) for var, num in brand_to_owner_test.columns]

	for ii in range(2,max_num_owner+1):
		overlap_or_gap = (brand_to_owner_test['start_year_' + str(ii)] < brand_to_owner_test['end_year_' + str(ii-1)]) | \
			((brand_to_owner_test['start_year_' + str(ii)] == brand_to_owner_test['end_year_' + str(ii-1)]) & \
			(brand_to_owner_test['start_month_' + str(ii)] != (brand_to_owner_test['end_month_' + str(ii-1)] + 1))) | \
			((brand_to_owner_test['start_year_' + str(ii)] > brand_to_owner_test['end_year_' + str(ii-1)]) & \
			((brand_to_owner_test['start_month_' + str(ii)] != 1) | (brand_to_owner_test['end_month_' + str(ii-1)] != 12)))
		if overlap_or_gap.sum() > 0:
			brand_to_owner_test['overlap'] = overlap_or_gap
			indices = brand_to_owner_test[brand_to_owner_test['overlap'] != 0].index.tolist()
			for index in indices:
				print(brand_to_owner_test.loc[index])
			raise Exception('There are gaps or overlap in the ownership mapping.')

	# Merge on brand and date intervals
	if month_or_quarter == 'month':
		brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
		brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
		df['date'] = pd.to_datetime(dict(year=df.year, month=df.month, day=1))
		if add_dhhi:
			sqlcode = '''
			select df.upc, df.year, df.month, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
		else:
			sqlcode = '''
			select df.upc, df.year, df.month, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
	elif month_or_quarter == 'quarter':
		brand_to_owner.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner['start_month']/3)-1)+1
		brand_to_owner.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, brand_to_owner.end_year, brand_to_owner.end_year - 1)
		brand_to_owner.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, 3*(np.floor(brand_to_owner.end_month/3)), 12)
		brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
		brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
		df['date'] = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1))
		if add_dhhi:
			sqlcode = '''
			select df.upc, df.year, df.quarter, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
		else:
			sqlcode = '''
			select df.upc, df.year, df.quarter, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
	df_own = ps.sqldf(sqlcode,locals())
	return df_own

def append_owners_brandlevel(code, df, month_or_quarter,add_dhhi = False):
	# # Load list of UPCs and brands
	# brands = pd.read_csv('../../../../All/m_' + code + '/intermediate/brands.csv', delimiter = ',', index_col = 'upc')
	# upcs = upcs['brand_code_uc']
	# upc_map = upcs.to_dict()

	# # Map brands to dataframe (by UPC)
	# df['brand_code_uc'] = df['upc'].map(upc_map)

	# Load ownership assignments
	brand_to_owner = pd.read_csv('../../../../All/m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')

	# Assign min/max year and month when listed as zero in ownership mapping
	min_year = df['year'].min()
	max_year = df['year'].max()

	if month_or_quarter == 'month':
		min_month = df.loc[df['year']==min_year,'month'].min()
		max_month = df.loc[df['year']==max_year,'month'].max()
	elif month_or_quarter == 'quarter':
		min_month = (3*(df.loc[df['year']==min_year,'quarter']-1)+1).min()
		max_month = (3*df.loc[df['year']==max_year,'quarter']).max()

	# Remove Onwership that starts later than the latest time in the dataframe
	brand_to_owner = brand_to_owner[(brand_to_owner['start_year'] < max_year) | ((brand_to_owner['start_year'] == max_year)&(brand_to_owner['start_month'] <= max_month))]
	# Remove Onwership that ends earlier than the earliest time in the dataframe
	brand_to_owner = brand_to_owner[(brand_to_owner['end_year'] > min_year) | ((brand_to_owner['end_year'] == min_year)&(brand_to_owner['end_month'] >= min_month)) | (brand_to_owner['end_year'] == 0)]

	brand_to_owner.loc[(brand_to_owner['start_month']==0) | (brand_to_owner['start_year']<min_year) | ((brand_to_owner['start_year']==min_year)&(brand_to_owner['start_month']<min_month)),'start_month'] = min_month
	brand_to_owner.loc[(brand_to_owner['start_year']==0) | (brand_to_owner['start_year']<min_year),'start_year'] = min_year
	brand_to_owner.loc[(brand_to_owner['end_month']==0) | (brand_to_owner['end_year']>max_year) | ((brand_to_owner['end_year']==max_year)&(brand_to_owner['end_month']>max_month)),'end_month'] = max_month
	brand_to_owner.loc[(brand_to_owner['end_year']==0) | (brand_to_owner['end_year']>max_year),'end_year'] = max_year

	# Throw error if (1) dates don't span the entirety of the sample period or
	# (2) ownership dates overlap
	brand_to_owner_test = brand_to_owner.copy()
	brand_to_owner_test = brand_to_owner_test.sort_values(by=['brand_code_uc', 'start_year', 'start_month'])

	if month_or_quarter == 'month':
		min_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).min()
		max_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).max()
		brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
		brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))
	elif month_or_quarter == 'quarter':
		min_date = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1)).min()
		max_date = pd.to_datetime(dict(year=df.year, month=3*df.quarter, day=1)).max()
		brand_to_owner_test.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner_test['start_month']/3)-1)+1
		brand_to_owner_test.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, brand_to_owner_test.end_year, brand_to_owner_test.end_year - 1)
		brand_to_owner_test.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, 3*(np.floor(brand_to_owner_test.end_month/3)), 12)
		brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
		brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))

	brand_dates = brand_to_owner_test.groupby('brand_code_uc')[['start_date_test', 'end_date_test']].agg(['min', 'max'])
	if ((brand_dates.start_date_test['min']!=min_date).sum() + (brand_dates.end_date_test['max']!=max_date).sum() > 0):
		print('Ownership definitions does not span the entire sample period:')
		for index, row in brand_dates.iterrows():
			if row.start_date_test['min'] != min_date or row.end_date_test['max'] != max_date:
				print(index)
				print('start_date: ', row.start_date_test['min'])
				print('end_date: ', row.end_date_test['max'])

	brand_to_owner_test['owner_num'] = brand_to_owner_test.groupby('brand_code_uc').cumcount()+1
	max_num_owner = brand_to_owner_test['owner_num'].max()
	brand_to_owner_test = brand_to_owner_test.set_index('owner_num',append=True)
	brand_to_owner_test = brand_to_owner_test.unstack('owner_num')
	brand_to_owner_test.columns = ['{}_{}'.format(var, num) for var, num in brand_to_owner_test.columns]

	for ii in range(2,max_num_owner+1):
		overlap_or_gap = (brand_to_owner_test['start_year_' + str(ii)] < brand_to_owner_test['end_year_' + str(ii-1)]) | \
			((brand_to_owner_test['start_year_' + str(ii)] == brand_to_owner_test['end_year_' + str(ii-1)]) & \
			(brand_to_owner_test['start_month_' + str(ii)] != (brand_to_owner_test['end_month_' + str(ii-1)] + 1))) | \
			((brand_to_owner_test['start_year_' + str(ii)] > brand_to_owner_test['end_year_' + str(ii-1)]) & \
			((brand_to_owner_test['start_month_' + str(ii)] != 1) | (brand_to_owner_test['end_month_' + str(ii-1)] != 12)))
		if overlap_or_gap.sum() > 0:
			brand_to_owner_test['overlap'] = overlap_or_gap
			indices = brand_to_owner_test[brand_to_owner_test['overlap'] != 0].index.tolist()
			for index in indices:
				print(brand_to_owner_test.loc[index])
			raise Exception('There are gaps or overlap in the ownership mapping.')

	# Merge on brand and date intervals
	if month_or_quarter == 'month':
		brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
		brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
		df['date'] = pd.to_datetime(dict(year=df.year, month=df.month, day=1))
		if add_dhhi:
			sqlcode = '''
			select df.year, df.month, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
		else:
			sqlcode = '''
			select df.year, df.month, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
	elif month_or_quarter == 'quarter':
		brand_to_owner.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner['start_month']/3)-1)+1
		brand_to_owner.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, brand_to_owner.end_year, brand_to_owner.end_year - 1)
		brand_to_owner.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, 3*(np.floor(brand_to_owner.end_month/3)), 12)
		brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
		brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
		df['date'] = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1))
		if add_dhhi:
			sqlcode = '''
			select df.year, df.quarter, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
		else:
			sqlcode = '''
			select df.year, df.quarter, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
			from df
			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
			'''
	df_own = ps.sqldf(sqlcode,locals())
	return df_own

def adjust_inflation(df, all_vars, month_or_quarter, rename_var = True):

	# Import CPIU dataset
	cpiu = pd.read_excel('../../../../All/master/cpiu_2000_2020.xlsx', header = 11)
	cpiu = cpiu.set_index('Year')
	month_dictionary = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
	cpiu = cpiu.rename(columns = month_dictionary)
	cpiu = cpiu.drop(['HALF1','HALF2'], axis=1)
	cpiu = cpiu.stack()

	# Aggregate to the quarter level, if necessary
	cpiu = cpiu.reset_index().rename(columns = {'level_1':'month',0:'cpiu'})
	if month_or_quarter == 'quarter':
		cpiu['quarter'] = cpiu['month'].apply(lambda x: 1 if x <=3 else 2 if ((x>3) & (x<=6)) else 3 if ((x>6) & (x<=9)) else 4)
		cpiu = cpiu.groupby(['Year', month_or_quarter]).agg({'cpiu': 'mean'}).reset_index()
	if month_or_quarter == 'month':
		cpiu = cpiu.set_index(['Year', month_or_quarter]).reset_index()

	# Set index value in base period
	cpiu['cpiu_201001'] = float(cpiu.loc[(cpiu['Year'] == 2010) & (cpiu[month_or_quarter]==1),'cpiu'])
	cpiu = cpiu.rename(columns={'Year': 'year'})
	cpiu = cpiu.set_index(['year', month_or_quarter])

	# Merge CPIU onto dataframe and adjust prices
	df = df.join(cpiu, on=['year', month_or_quarter], how = 'left')
	for var in all_vars:
		if rename_var:
			df[var] = df[var] * (df['cpiu_201001'] / df['cpiu'])
		else:
			df[var + '_adj'] = df[var] * df['cpiu_201001'] / df['cpiu']
	df = df.drop(['cpiu_201001', 'cpiu'], axis = 1)
	return df

def load_problem_results(code, results_pickle, month_or_quarter):

	# Create fake formulation that is just a logit
	product_data = pd.read_csv(pyblp.data.NEVO_PRODUCTS_LOCATION)
	logit_formulation = pyblp.Formulation('prices')
	problem = pyblp.Problem(logit_formulation, product_data)
	results = problem.solve()

	# Create the real problem
	df, characteristics, nest, num_instruments, add_differentiation, add_blp = gather_product_data(code, month_or_quarter)
	formulation_char, formulation_fe, df = create_formulation(code, df, chars,
		nests = nest, month_or_quarter = month_or_quarter,
		num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp)

	if something:
		real_problem = pyblp.Problem(formulation_char)
	elif something:
		real_problem = pyblp.Problem(formulation_fe)
	elif something:
		real_problem = pyblp.Problem((formulation_fe, formulation_char), integration = integration)

	results.problem = real_problem
	results_dict = pickle.load(open(results_pickle, 'rb'))
	for k in results_dict.keys():
		setattr(results, k, results_dict[k])


	return results, df
