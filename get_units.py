import re
import sys
from datetime import datetime
import unicodecsv as csv
import auxiliary as aux
import tqdm
import os

def generate_units_table(code, years, groups, modules):

	with open('m_' + code + '/intermediate/units.csv', "wb") as csvfile:
		header = ["group", "module", "units", "count", "median", "mode"]
		writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
		writer.writerow(header)

		for group, module in zip(groups, modules):

			all_units_frequency_list = []

			for year in years:
				movement_table = aux.load_chunked_year_module_movement_table(year, group, module)
				
				for data_chunk in tqdm(movement_table):
					# normunits is the total volume sold (quantity x size)
					data_chunk = data_chunk[['size1_amount', 'size1_units', 'units', 'prmult']]
					data_chunk['normunits'] = data_chunk['units'] / data_chunk['prmult']
					data_chunk = data_chunk[['size1_amount', 'size1_units', 'norm_units']]
					units_frequency = data_chunk.groupby(['size1_amount', 'size1_units']).sum()
					units_frequency['normunits'] = units_frequency['normunits'] * units_frequency['size1_units']
					all_units_frequency_list.append(units_frequency)

			# Sum frequency table to get the total frequency table
			all_units_frequency = pd.concat(all_units_frequency_list)
			agg_all_units_frequency = all_units_frequency.groupby(['size1_amount', 'size1_units']).sum()

			unique_units = agg_all_units_frequency['size1_units'].unique()

			for unit in unique_units:
				this_unit = agg_all_units_frequency[agg_all_units_frequency['size1_units'] == unit]
				this_unit = this_unit.sort_values(by = ['size1_amount'])

				# Weighted by quantity, what is the median package size?
				median_quantity = 0.5 * this_unit['normunits'].sum()
				booleans = this_unit['normunits'].cumsum() <= median_quantity
				median = this_unit.size1_amount[sum(booleans)]

				# Mode
				where_mode = this_unit.normunits.idxmax()
				mode = this_unit.size1_amount[where_mode]

				to_write = [group, module, unit, median, mode]
				writer.writerow(to_write)

code = sys.argv[1]
info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateCompleted"])

if not os.path.isdir('m_' + code + '/intermediate'):
	print("Making the intermediate directory")
	os.makedirs('m_' + code + '/intermediate')
generate_units_table(code, years, groups, modules)
