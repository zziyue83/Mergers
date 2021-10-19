import re
import sys
from datetime import datetime
import auxiliary as aux
from tqdm import tqdm
import numpy as np
import pandas as pd
from clean_data import clean_data
import os

def parse_info(code):
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


def load_store_table(year):
	store_path = "../../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
	store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
	print("Loaded store file of "+ year)
	return store_table


def load_movement_table(year, group, module, path = ''):

	if path == '':
		path = "../../../Data/nielsen_extracts/RMS/" + year + "/Movement_Files/" + group + "_" + year + "/" + module + "_" + year + ".tsv"

	assert os.path.exists(path), "File does not exist: %r" % path

	table = pd.read_csv(path, delimiter = "\t")

	return table


def upc_list(code):

	path_input = "../../../All/" + code + "/intermediate"
	data = pd.read_csv(path_input + "/stata_did_int_month.csv")

	if 'owner_x' in data.columns and 'owner' not in data.columns:
		print('owner_x in data columns')
		data.rename(columns = {'owner_x': 'owner'}, inplace = True)

	elif 'owner' not in data.columns:
		print('owner not in data columns')
		stata_data = pd.read_csv(path_input + "/stata_did_month.csv")
		stata_data = stata_data[['year', 'upc', 'dma_code', 'month', 'owner']]
		data = pd.merge(data, stata_data, on=['year', 'upc', 'dma_code', 'month'], how='left')

	labels = ["multiple owners", "multiple", "Several owners", "Several Owners",
			  "several owners", "SEVERAL OWNERS", "Many owners", "MANY OWNERS",
			  "0", "Store Brands", "Store Brand", "VARIOUS OWNERS", "various owners",
			  "Ctl Br", "CTL BR", "Control Brands"]

	for label in labels:
		data.loc[data['owner']==label, "owner"] = "several owners"

	data.loc[data['brand_code_uc']==536746, "owner"] = "several owners"

	data = data[data['owner']=='several owners']

	data = data.groupby(['upc', 'owner'])['prices'].agg(['mean'])

	data.to_csv('../../../All/' + code + '/properties/store_upcs.csv', sep = ',', encoding = 'utf-8')


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


def merge(code):

	store_upcs = pd.read_csv('../../../All/' + code + '/properties/store_upcs.csv')

	if len(store_upcs)!=0:

		store_codes = pd.read_csv('../../../All/' + code + '/properties/store_codes.csv')
		did_data = pd.read_csv('../../../All/' + code + '/intermediate/stata_did_int_month.csv')
		did_data = pd.merge(did_data, store_codes, on=['year', 'upc', 'dma_code'], how='left')
		did_data.to_csv('../../../All/' + code + '/intermediate/stata_did_int_month.csv')


#folder = sys.argv[1]
#code = 'm_' + folder[15:]
log_out = open('output/store_brands.log', 'w')
log_err = open('output/store_brands.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

base_folder = '../../../All/'
folders = [folder for folder in os.listdir(base_folder)]

for folder in folders:
	print(folder)
	if os.path.exists(base_folder + folder + '/intermediate/stata_did_int_month.csv'):
		print('for loop :' + folder)
		info_dict = parse_info(folder)
		groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
		groups = [str(0) + str(group) if len(str(group)) == 3 else group for group in groups]
		years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])
		upc_list(folder)
		store_list(folder, years, groups, modules, info_dict["DateAnnounced"], info_dict["DateCompleted"])
		merge(folder)

