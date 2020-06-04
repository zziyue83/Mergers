import re
import sys
from datetime import datetime
import unicodecsv as csv
import auxiliary as aux
import tqdm

def generate_units_table(code, years, groups, modules):

	with open('m_' + code + '/intermediate/units.csv', "wb") as csvfile:
		header = ["group", "module", "units", "count", "median", "mode"]
		writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
		writer.writerow(header)

		for group, module in zip(groups, modules):

			all_units_frequency_list = []

			for year in years:
				movement_table = aux.load_chunked_year_module_movement_table(year, group, module)
				
				for data_chunk in tqdm(movementTable):
					# Get the frequency table of units
					# FIX THIS!!! It should be total volume sold = quantity * size, NOT count!!!
					units_frequency = movement_table.groupby(['size1_amount', 'size1_units']).count()
					all_units_frequency_list.append(units_frequency)

			# Sum frequency table to get the total frequency table
			all_units_frequency = pd.concat(all_units_frequency_list)
			agg_all_units_frequency = all_units_frequency.groupby(['size1_amount', 'size1_units']).sum()

			unique_units = agg_all_units_frequency['size1_units'].unique()

			for unit in unique_units:
				this_unit = agg_all_units_frequency[agg_all_units_frequency['size1_units'] == unit]

				median = GET MEDIAN

				# CHECK THIS -- figure out how argmax works
				where_mode = this_unit.argmax()
				where_mode = where_mode[0] # do I need this?
				mode = this_unit.size1_amount[where_mode]

				to_write = [group, module, unit, median, mode]
				writer.writerow(to_write)



code = sys.argv[1]
info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateCompleted"])
generate_units_table(code, years, groups, modules)

print(info_dict)
print(groups)
print(modules)
print(years)