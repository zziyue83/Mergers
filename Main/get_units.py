import re
import sys
from datetime import datetime
import unicodecsv as csv
import auxiliary as aux
from tqdm import tqdm
import os
import pandas as pd
import numpy as np
from clean_data import clean_data

def generate_units_table(code, years, groups, modules, merger_date, pre_months = 24, post_months = 24):

	# Get the relevant range
	dt = datetime.strptime(merger_date, '%Y-%m-%d')
	month_int = dt.year * 12 + dt.month
	min_year, min_month = aux.int_to_month(month_int - pre_months)
	max_year, max_month = aux.int_to_month(month_int + post_months)

	#manual fix for baby food- strained
	if ((code=='1817013020_3') & (max_year > 2008)):
		max_year = 2008
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2008, years))

	#manual fix for bread
	if ((code=='2203820020_1') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for buns
	if ((code=='2203820020_2') & (max_year > 2008)):
		max_year = 2012
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for rolls
	if ((code=='2203820020_3') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for pies
	if ((code=='2203820020_8') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2012, years))

	#manual fix for bakery-remaining
	if ((code=='2203820020_10') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2012, years))

		#manual fix for cheesecake
	if ((code=='2203820020_11') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2012, years))

		#manual fix for biscuits
	if ((code=='2203820020_12') & (max_year > 2012)):
		max_year = 2012
		max_month = 12
		years = list(filter(lambda x: int(x) <= 2012, years))

		#manual fix for RBC_Bread
	if ((code=='2033113020_2') & (int(years[0]) < 2007)):
		min_year = 2007
		min_month = 1
		years = years[1:]
		print('entering here')

		#manual fix for RBC_Cake
	if ((code=='2033113020_3') & (int(years[0]) < 2007)):
		min_year = 2007
		min_month = 1
		years = years[1:]

		#manual fix for Headache Pills
	if ((code=='2373087020_1') & (int(years[0]) < 2010)):
		min_year = 2010
		min_month = 1
		years = years[1:]

	product_map = aux.get_product_map(list(set(groups)))
	add_from_map = ['size1_units', 'size1_amount', 'multi']

	with open('../../../All/m_' + code + '/intermediate/units.csv', "wb") as csvfile:
		header = ["units", "total_quantity", "median", "mode"]
		writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
		writer.writerow(header)

		all_units_frequency_list = []
		print("now loading nielsen data")
		iterations = 0

		for group, module in zip(groups, modules):

			for year in years:
				movement_table = aux.load_chunked_year_module_movement_table(year, group, module)
				upc_ver_map = aux.get_upc_ver_uc_map(year)

				for data_chunk in tqdm(movement_table):
					# First make sure that only the actual years and months are included
					print(data_chunk.head())
					print(data_chunk.columns)
					iterations += 1
					if int(year) == min_year or int(year) == max_year:
						data_chunk['month'] = np.floor((data_chunk['week_end'] % 10000)/100).astype(int)
						if int(year) == min_year:
							data_chunk = data_chunk[data_chunk.month >= min_month]
						else:
							data_chunk = data_chunk[data_chunk.month <= max_month]

					data_chunk['upc_ver_uc'] = data_chunk['upc'].map(upc_ver_map)
					data_chunk = data_chunk.join(product_map[add_from_map], on=['upc','upc_ver_uc'], how='left')

					data_chunk = clean_data(code, data_chunk)
					data_chunk = data_chunk[['size1_amount', 'size1_units', 'units', 'multi']]

					# normunits is the total volume sold (quantity x size)
					data_chunk['norm_units'] = data_chunk['units'] * data_chunk['multi'] * data_chunk['size1_amount']
					data_chunk['norm_size1_amount'] = data_chunk['size1_amount'] * data_chunk['multi']
					data_chunk = data_chunk[['norm_size1_amount', 'size1_units', 'norm_units']]
					units_frequency = data_chunk.groupby(['norm_size1_amount', 'size1_units']).sum()
					all_units_frequency_list.append(units_frequency)

		# Sum frequency table to get the total frequency table
		print(iterations)
		all_units_frequency = pd.concat(all_units_frequency_list)
		print(all_units_frequency.head())
		print(all_units_frequency.columns)
		agg_all_units_frequency = all_units_frequency.groupby(['norm_size1_amount', 'size1_units']).sum()
		agg_all_units_frequency = agg_all_units_frequency.reset_index()
		agg_all_units_frequency = agg_all_units_frequency.sort_values(by = 'size1_units')
		agg_all_units_frequency.to_csv('../../../All/m_' + code + '/intermediate/units_frequency.csv', sep = ',', index = False)
		unique_units = agg_all_units_frequency['size1_units'].unique()

		print("finished aggregation")
		for unit in unique_units:
			print(unit)
			this_unit = agg_all_units_frequency[agg_all_units_frequency['size1_units'] == unit]
			this_unit = this_unit.sort_values(by = ['norm_size1_amount'])

			# Weighted by quantity, what is the median package size?
			total_quantity = this_unit['norm_units'].sum()
			booleans = this_unit['norm_units'].cumsum() <= (0.5 * total_quantity)
			# median = this_unit.norm_size1_amount[sum(booleans)]
			this_unit_np = np.array(this_unit['norm_size1_amount'])
			median = this_unit_np[sum(booleans)]

			# Mode
			where_mode = this_unit.norm_units.idxmax()
			mode = this_unit.norm_size1_amount[where_mode]

			to_write = [unit, total_quantity, median, mode]
			writer.writerow(to_write)

code = sys.argv[1]
if not os.path.isdir('../../../All/m_' + code + '/output'):
	os.makedirs('../../../All/m_' + code + '/output')
log_out = open('../../../All/m_' + code + '/output/get_units.log', 'w')
log_err = open('../../../All/m_' + code + '/output/get_units.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = aux.parse_info(code)

merger_date = info_dict['DateCompleted']
groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

if not os.path.isdir('../../../All/m_' + code + '/intermediate'):
	print("Making the intermediate directory")
	os.makedirs('../../../All/m_' + code + '/intermediate')
generate_units_table(code, years, groups, modules, merger_date)

print("get_units finished successfully")
log_out.close()
log_err.close()
