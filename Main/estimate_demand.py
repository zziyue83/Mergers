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
		i += 1

	return df, i

def estimate_demand(code, df, chars, nests = None, month_or_quarter = 'month', estimate_type = 'logit', num_instruments = 0, add_differentiation = False, add_blp = False):

	df['market_ids'] = df['dma_code'].astype(str) + '_' + df[month_or_quarter].astype(str)
	df['firm_ids'] = df['owner']

	# Baseline formulation
	num_chars = 2
	string_chars = '1 + prices'
	for this_char in chars:
		string_chars = string_chars + ' + ' this_char
		num_chars += 1
	formulation_char = pyblp.Formulation(string_chars, absorb = 'C(TIME) + C(dma_code)')
	formulation_fe = pyblp.Formulation('0 + prices', absorb = 'C(upc) + C(TIME) + C(dma_code)')

	# Add instruments
	if add_differentiation:
		gandhi_houde = pyblp.build_differentiation_instruments(formulation_char, df)
		for i in range(gandhi_houde.shape[1]):
			df['demand_instruments' + str(num_instruments)] = gandhi_houde[:,i]
			num_instruments += 1

	if add_blp:
		blp = pyblp.build_blp_instruments(formulation_char, df)
		for i in range(blp.shape[1]):
			df['demand_instruments' + str(num_instruments)] = blp[:,i]
			num_instruments += 1

	if nests is not None:
		# Add the nests
		if nests == 'inside':
			df['nesting_ids'] = 1
		else:
			df['nesting_ids'] = ???


	# Get the first stage of instruments


	

	# Estimate
	if estimate_type == 'logit':

		problem_char = pyblp.Problem(formulation_char, df)
		problem_fe = pyblp.Problem(formulation_fe, df)

		results_char = problem_char.solve()
		results_fe = problem_char.solve()

	elif estimate_type == 'blp':
		
		forumlation_blp = (formulation_fe, formulation_char)
		integration = pyblp.Integration(integration_options['type'], size = integration_options['size'])
		if use_knitro:
			optimization = pyblp.Optimization()
		else:
			optimization = 

		problem = pyblp.Problem(formulation_blp, df, integration = integration)
		results_blp = problem.solve(sigma = np.ones((num_chars, num_chars)), optimization = bfgs)

	else:
		print("Did not run estimation")


	

code = sys.argv[1]
month_or_quarter = sys.argv[2]
estimate_type = sys.argv[3]

info_dict = aux.parse_info(code)
characteristics = aux.get_characteristics(info_dict["Characteristics"])
nest = aux.get_nest(info_dict["Nest"])
if (nest is not None) and (nest not in characteristics):
	to_append = characteristics
else:
	to_append = characteristics.append(nest)

# Get the characteristics map
char_df = pd.read_csv('m_' + code + '/properties/characteristics.csv', delimiter = ',', index_col = 'brand_code_uc')
char_map = char_df.to_dict()

df = pd.read_csv('m_' + code + '/intermediate/data_' + month_or_quarter + '.csv', delimiter = ',')
df = aux.append_owners(code, df)
df = add_characteristics(code, cf, char_map, to_append)
df, num_instruments = add_instruments(code, df, instrument_names)
estimate_demand(code, df, characteristics, nests = nest, month_or_quarter = month_or_quarter, estimate_type = estimate_type, num_instruments = num_instruments)

