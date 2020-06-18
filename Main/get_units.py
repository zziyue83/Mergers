import re
import sys
from datetime import datetime
import unicodecsv as csv
import auxiliary as aux
from tqdm import tqdm
import os
import pandas as pd
import numpy as np

def generate_units_table(code, years, groups, modules, merger_date, pre_months = 18, post_months = 18):

	# Get the relevant range
	dt = datetime.strptime(merger_date, '%Y-%m-%d')
	month_int = dt.year * 12 + dt.month
	min_year, min_month = aux.int_to_month(month_int - pre_months)
	max_year, max_month = aux.int_to_month(month_int + post_months)

	product_map = aux.get_product_map(list(set(groups)))
	add_from_map = ['size1_units', 'size1_amount', 'multi']

	with open('../../../All/m_' + code + '/intermediate/units.csv', "wb") as csvfile:
		header = ["units", "total_quantity", "median", "mode"]
		writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
		writer.writerow(header)

		all_units_frequency_list = []


		for group, module in zip(groups, modules):

			for year in years:
				movement_table = aux.load_chunked_year_module_movement_table(year, group, module)
				
				for data_chunk in tqdm(movement_table):
					# First make sure that only the actual years and months are included
					if int(year) == min_year or int(year) == max_year:
						data_chunk['month'] = np.floor((data_chunk['week_end'] % 10000)/100).astype(int)
						if int(year) == min_year:
							data_chunk = data_chunk[data_chunk.month >= min_month]
						else:
							data_chunk = data_chunk[data_chunk.month <= max_month]
					
					for to_add in add_from_map:
						data_chunk[to_add] = data_chunk['upc'].map(product_map[to_add])
					data_chunk = data_chunk[['size1_amount', 'size1_units', 'units', 'multi']]
					
					# normunits is the total volume sold (quantity x size)
					data_chunk['norm_units'] = data_chunk['units'] * data_chunk['multi'] * data_chunk['size1_amount']
					data_chunk['norm_size1_amount'] = data_chunk['size1_amount'] * data_chunk['multi']
					data_chunk = data_chunk[['norm_size1_amount', 'size1_units', 'norm_units']]
					units_frequency = data_chunk.groupby(['norm_size1_amount', 'size1_units']).sum()
					all_units_frequency_list.append(units_frequency)
				print("finished year "+str(year))

		# Sum frequency table to get the total frequency table
		all_units_frequency = pd.concat(all_units_frequency_list)
		agg_all_units_frequency = all_units_frequency.groupby(['norm_size1_amount', 'size1_units']).sum()
		print(agg_all_units_frequency)
		print(agg_all_units_frequency.columns)
		unique_units = agg_all_units_frequency['size1_units'].unique()

		print("finished aggregation")
		for unit in unique_units:
			this_unit = agg_all_units_frequency[agg_all_units_frequency['size1_units'] == unit]
			this_unit = this_unit.sort_values(by = ['norm_size1_amount'])

			# Weighted by quantity, what is the median package size?
			total_quantity = this_unit['norm_units'].sum()
			booleans = this_unit['norm_units'].cumsum() <= (0.5 * total_quantity)
			median = this_unit.norm_size1_amount[sum(booleans)]

			# Mode
			where_mode = this_unit.normunits.idxmax()
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
if code == '1912896020_1':
	years = ['2006','2007','2008','2009']
	print('beer data only lasts till 2009')

if not os.path.isdir('../../../All/m_' + code + '/intermediate'):
	print("Making the intermediate directory")
	os.makedirs('../../../All/m_' + code + '/intermediate')
generate_units_table(code, years, groups, modules, merger_date)

print("get_units finished successfully")
log_out.close()
log_err.close()