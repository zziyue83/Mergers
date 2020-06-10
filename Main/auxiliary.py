import re
import sys
from datetime import datetime
import pyblp
import pickle
import pandas as pd
import numpy as np

def parse_info(code):
	file = open('m_' + code + '/info.txt', mode = 'r')
	info_file = file.read()
	file.close()

	all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
	info_dict = {}
	for info in all_info_elements:
		info_name = info.group(1).strip()
		info_content = info.group(2).strip()
		info_dict[info_name] = info_content
	return info_dict

def get_groups_and_modules(full_string):
	all_group_module = re.finditer('{(.*?),(.*?)}', full_string, re.DOTALL)
	groups = []
	modules = []
	for pair in all_group_module:
		groups.append(pair.group(1).strip())
		modules.append(pair.group(2).strip())
	return groups, modules

def get_years(year_string, pre = 2, post = 2):
	dt = datetime.strptime(year_string, '%Y-%m-%d')
	years = []
	for i in range(-pre, post + 1, 1):
		this_year = dt.year + i
		if this_year >= 2006 and this_year <= 2017:
			years.append(str(this_year))
	return years

def get_merging_parties(info_str):
	all_parties = re.finditer('{(.*?)}', full_string, re.DOTALL)
	merging_parties = []
	for i in all_parties:
		merging_parties.append(i)
	return merging_parties

def load_chunked_year_module_movement_table(year, group, module, path = ''):
    if path == '':
        path = "../../../Data/nielsen_extracts/RMS/" + year + "/Movement_Files/" + group + "_" + year + "/" + module + "_" + year + ".tsv"
    table = pd.read_csv(path, delimiter = "\t", chunksize = 10000000)
    return table

def get_product_map(groups):
    products_path = "../../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
    products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = "upc")
    int_groups = [int(i) for i in groups]
	wanted_products = products[products['product_group_code'].isin(int_groups)]
	product_map = wanted_products.to_dict()
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

def append_owners(code, df, month_or_quarter):
	# Load list of UPCs and brands
	upcs = pd.read_csv('m_' + code + '/intermediate/upcs.csv', delimiter = ',', index_col = 'upc')
	upcs = upcs['brand_code_uc']
	upc_map = upcs.to_dict()

	# Map brands to dataframe (by UPC)
	df['brand_code_uc'] = df['upc'].map(upc_map['brand_code_uc'])

	# Load ownership assignments
	brand_to_owner = pd.read_csv('m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')
	max_num_owner = brand_to_owner['owner_num'].max()
	brand_to_owner = brand_to_owner.set_index(['brand_code_uc','owner_num'])
	brand_to_owner = brand_to_owner.unstack('owner_num')
	brand_to_owner.columns = ['{}_{}'.format(var, num) for var, num in brand_to_owner.columns]

	# Merge ownership
	df = df.join(brand_to_owner, on='brand_code_uc', how='left')
	min_year = df['year'].min()
	max_year = df['year'].max()

	for ii in reversed(range(1,max_num_owner+1)):
		df.loc[df['start_year_1']==0,'owner_'+str(ii)] = df.loc[df['start_year_1']==0,'owner_1']
		df.loc[df['start_year_1']==0,'end_month_'+str(ii)] = 12
		df.loc[df['start_year_1']==0,'end_year_'+str(ii)] = max_year
		df.loc[df['start_year_1']==0,'start_month_'+str(ii)] = 1
		df.loc[df['start_year_1']==0,'start_year_'+str(ii)] = min_year

	for ii in range(1,max_num_owner+1):
		if month_or_quarter == 'month':
			df.loc[((df['year'] > df['start_year_'+str(ii)]) | \
				((df['year']==df['start_year_'+str(ii)]) & (df['month'] >= df['start_month_'+str(ii)]))) & \
				(((df['year'] < df['end_year_'+str(ii)]) | \
				((df['year']==df['end_year_'+str(ii)]) & df['month'] <= df['end_year_'+str(ii)]))),'owner'] = \
				df.loc[((df['year'] > df['start_year_'+str(ii)]) | \
				((df['year']==df['start_year_'+str(ii)]) & (df['month'] >= df['start_month_'+str(ii)]))) & \
				(((df['year'] < df['end_year_'+str(ii)]) | \
				((df['year']==df['end_year_'+str(ii)]) & df['month'] <= df['end_year_'+str(ii)]))),'owner_'+str(ii)]
		elif month_or_quarter == 'quarter':
			df.loc[((df['year'] > df['start_year_'+str(ii)]) | \
				((df['year']==df['start_year_'+str(ii)]) & (df['quarter'] >= ceil(df['start_month_'+str(ii)]/3)))) & \
				(((df['year'] < df['end_year_'+str(ii)]) | \
				((df['year']==df['end_year_'+str(ii)]) & df['quarter'] <= ceil(df['end_year_'+str(ii)]/3)))),'owner'] = \
				df.loc[((df['year'] > df['start_year_'+str(ii)]) | \
				((df['year']==df['start_year_'+str(ii)]) & (df['quarter'] >= ceil(df['start_month_'+str(ii)]/3)))) & \
				(((df['year'] < df['end_year_'+str(ii)]) | \
				((df['year']==df['end_year_'+str(ii)]) & df['quarter'] <= ceil(df['end_year_'+str(ii)]/3)))),'owner_'+str(ii)]

	return(df)

def adjust_inflation(df, var, month_or_quarter):

	# Import CPIU dataset
	month_or_quarter = 'month'
	cpiu = pd.read_excel('../Data/cpiu_2000_2020.xlsx', header = 11)
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
	cpiu['cpiu_202001'] = float(cpiu.loc[(cpiu['Year']==2020) & (cpiu[month_or_quarter]==1),'cpiu'])
	cpiu = cpiu.rename(columns={'Year': 'year'})
	cpiu = cpiu.set_index(['year','month'])

	# Merge CPIU onto dataframe and adjust prices
	df = df.join(cpiu, on=['year',month_or_quarter], how='left')
	df[var + '_adj'] = df[var]*(df['cpiu_202001']/df['cpiu'])

	return(df)

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
