try_1.py

import pandas as pd

code = 2823116020

# using parse_info to check information
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

# headers from data_month that will be used
info_needed = ['upc','dma_code', 'year', 'month', 'sales', 'volume']

# opening the dataframe and using only info needed
short_data_month = (pd.read_csv('../../../All/m_' + code + '/intermediate/data_month.csv')[info_needed]

# saving as new file
short_data_month.to_csv('short_data_month.csv', index = False, sep = ',', encoding = 'utf-8')