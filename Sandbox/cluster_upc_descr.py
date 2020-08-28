import re
import sys
from datetime import datetime
import pyblp
import pickle
import pandas as pd
import numpy as np
import pandasql as ps
import os


def get_product_map(groups):
	products_path = "../../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
	products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = ["upc","upc_ver_uc"])
	int_groups = [int(i) for i in groups]
	wanted_products = products[products['product_group_code'].isin(int_groups)]
	product_map = wanted_products
	return product_map

def get_groups_and_modules(full_string):
	all_group_module = re.finditer('{(.*?),(.*?)}', full_string, re.DOTALL)
	groups = []
	modules = []
	for pair in all_group_module:
		groups.append(pair.group(1).strip())
		modules.append(pair.group(2).strip())
	return groups, modules

def parse_info(code):
	file = open('../../../All/m_' + code + '/info.txt', mode = 'r')
	info_file = file.read()
	file.close()

	all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
	info_dict = {}
	for info in all_info_elements:
		info_name = info.group(1).strip()
		info_content = info.group(2).strip()
		info_dict[info_name] = info_content
	return info_dict

# test with merger ID 3035705020_13, Cosmetics-nail polish,
# code = sys.argv[1]
# code = '3035705020_13'
if not os.path.isdir('../../../All/m_' + code + '/output'):
	os.makedirs('../../../All/m_' + code + '/output')
log_out = open('../../../All/m_' + code + '/output/cluster_upc_descr.log', 'w')
log_err = open('../../../All/m_' + code + '/output/cluster_upc_descr.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = parse_info(code)
groups, modules = get_groups_and_modules(info_dict["MarketDefinition"])
product_map = get_product_map(list(set(groups)))
print(product_map['upc_descr'].unique())
print(len(product_map['upc_descr'].unique()))
