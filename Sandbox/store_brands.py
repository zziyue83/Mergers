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
	data = pd.read_csv(path_input + "/stata_did_int_month.csv",
                       delimiter=',', index_col=['upc', 'dma_code', 'year', 'month'])

	labels = ["multiple owners", "multiple", "Several owners", "Several Owners",
			  "several owners", "SEVERAL OWNERS", "Many owners", "MANY OWNERS",
			  "0", "Store Brands", "Store Brand", "VARIOUS OWNERS", "various owners",
			  "Ctl Br", "CTL BR", "Control Brands"]

	for label in labels:
		data.loc[data['owner']==label, "owner"] = "several owers"

	data.loc[data['brand_code_uc']==536746, "owner"] = "several owners"

	data = data[data['owner']=='several owners']

	data = data.groupby(['upc', 'owner'])['prices'].agg(['mean'])

	data.to_csv('../../../All/' + code + '/properties/store_upcs.csv', sep = ',', encoding = 'utf-8')


def store_list(code, years, groups, modules):

	# upc list has 'upc', 'owner'
	store_upcs = pd.read_csv('../../../All/' + code + '/properties/store_upcs.csv', sep = ',', encoding = 'utf-8')

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

				# df1 has 'upc', 'store_code_uc'
				df1 = df1.append(movement_table.groupby(['upc', 'store_code_uc'])['price'].agg(['mean']).reset_index())

		# all store upcs and their store_code_uc
		print(df1.columns)
		print(store_upcs.columns)
		df1 = pd.merge(store_upcs, df1, on='upc', how='inner').reset_index()

		# all store_code_uc, parent_code, and dma_code
		print(df2.columns)
		df2 = df2.groupby(['store_code_uc', 'parent_code', 'dma_code'])['year'].agg(['mean']).reset_index()

		# merge upc (store brands) and 'store_code_uc' with 'parent_code' and 'dma_code' data
		df1 = pd.merge(df1, df2, on='store_code_uc', how='inner')
		df1 = df1.drop(['Unnamed: 0', 'index', 'mean_x', 'mean_y', 'mean'], axis=1)
		df1 = df1.drop_duplicates(['upc', 'parent_code', 'dma_code'])

		# save to csv
		df1.to_csv('../../../All/' + code + '/properties/store_codes.csv', sep = ',', encoding = 'utf-8')


def merge(code):

	store_codes = pd.read_csv('../../../All/' + code + '/properties/store_codes.csv')
	did_data = pd.read_csv('../../../All/' + code + '/intermediate/stata_did_int_month.csv')

code = sys.argv[1]
log_out = open('output/store_brands.log', 'w')
log_err = open('output/store_brands.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

upc_list(code)
store_list(code, years, groups, modules)

