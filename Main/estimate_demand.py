import re
import sys
from datetime import datetime
import auxiliary as aux
import pyblp

def add_characteristics(code, df, char_map, chars):
	for this_char in chars:
		df[this_char] = df['brand_code_uc'].map(char_map[this_char])
	return df

def add_instruments(code, df, instrument_names):
	# First get the distances

	# Then get diesel prices to multiply
	df['demand_instruments0'] = df['distance'] * df['diesel']
	df = df.drop(['distance', 'diesel'])

	# Then get 
	i = 1
	for instrument in instrument_names:
		do something
		df['demand_instruments' + str(i)] = something
		i = i + 1

	return df, i

def estimate_demand(code, df, chars, nests = None, month_or_quarter = 'month', estimate_type = 'logit', num_instruments = None, add_differentiation = False, add_blp = False):

	df['market_ids'] = df['dma_code'].astype(str) + '_' + df[month_or_quarter].astype(str)

	# Get the first stage of instruments

	# Run logit
	logit_string_chars = '1 + prices'
	for this_char in chars:
		logit_string_chars = logit_string_chars + ' + ' this_char
	logit_formulation_char = pyblp.Formulation(logit_string_chars, absorb = 'C(TIME) + C(dma_code)')
	logit_formulation_fe = pyblp.Formulation('0 + prices', absorb = 'C(upc) + C(TIME) + C(dma_code)')

	if nests is not None:
		# Add the nests
		if nests == 'inside':
			df['nesting_ids'] = 1
		else:
			df['nesting_ids'] = ???

	if estimate_type == 'logit':

		problem_char = pyblp.Problem(logit_formulation_char, df)
		problem_fe = pyblp.Problem(logit_formulation_fe, df)

		results_char = logit_problem_char.solve()
		results_fe = logit_problem_char.solve()

	elif estimate_type == 'blp':

		hello

	else:
		
		ERROR


	

code = sys.argv[1]
info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateCompleted"])

conversion_map = get_conversion_map(code, info_dict["FinalUnit"])
area_month_upc = aggregate_movement(code, years, groups, modules, "month", conversion_map)
area_quarter_upc = aggregate_movement(code, years, groups, modules, "quarter", conversion_map)

acceptable_upcs = get_acceptable_upcs(area_month_upc['upc', 'shares'], float(info_dict["InitialShareCutoff"]))

# Find the unique brands associated with the acceptable_upcs and spit that out into brands.csv
# Get the UPC information you have for acceptable_upcs and spit that out into upc_dictionary.csv
write_brands_upc(code, area_month_upc, acceptable_upcs)

# Now filter area_month_upc and area_quarter_upc so that only acceptable_upcs survive
# Print out data_month.csv and data_quarter.csv
write_base_dataset(code, area_month_upc, acceptable_upcs, 'month')
write_base_dataset(code, area_quarter_upc, acceptable_upcs, 'quarter')

# Aggregate data_month (sum shares) by dma-month to get total market shares and spit that out as market_coverage.csv
write_market_coverage(code, area_month_upc, acceptable_upcs)

# How do you do Nielsen Characteristics excel file?


