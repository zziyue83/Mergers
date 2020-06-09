import re
import sys
from datetime import datetime

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

def append_owners(code, df):
	upcs = pd.read_csv('m_' + code + '/intermediate/upcs.csv', delimiter = ',', index_col = 'upc')
	upcs = upcs['brand_code_uc']
	upc_map = upcs.to_dict()

	df['brand_code_uc'] = df['upc'].map(upc_map['brand_code_uc'])

	brand_to_owner = pd.read_csv('m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')

	FINISH THIS WITH NEW FORMAT!!