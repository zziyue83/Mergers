import re
import sys
from datetime import datetime
import auxiliary as aux
import pandas as pd
import numpy as np
import pyblp
import pyhdfe
import statsmodels.api as sm
import pickle

# Set pyblp options
pyblp.options.digits = 3
pyblp.options.verbose = True
pyblp.options.flush_output = True

def add_characteristics(code, df, char_map, chars):
	for this_char in chars:
		df[this_char] = df['brand_code_uc'].map(char_map[this_char])
	return df

def add_instruments(code, df, instrument_names):
	# First get the distances
	distances = pd.read_csv('m_' + code + '/intermediate/distances.csv', delimiter = ',')

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

def gather_product_data(code):
	info_dict = aux.parse_info(code)
	characteristics = aux.get_characteristics(info_dict["Characteristics"])
	nest = aux.get_nest(info_dict["Nest"])
	instrument_names = aux.get_instruments(info_dict["Instruments"])

	if (nest is not None) and (nest not in characteristics):
		to_append = characteristics
	else:
		to_append = characteristics.append(nest)

	# Get the characteristics map
	char_df = pd.read_csv('m_' + code + '/properties/characteristics.csv', delimiter = ',', index_col = 'upc')
	char_map = char_df.to_dict()

	df = pd.read_csv('m_' + code + '/intermediate/data_' + month_or_quarter + '.csv', delimiter = ',')
	df = aux.append_owners(code, df)
	df = add_characteristics(code, cf, char_map, to_append)
	df, characteristics, nest, num_instruments = add_instruments(code, df, instrument_names)

def create_formulation(code, df, chars, nests = None, month_or_quarter = 'month',
	num_instruments = 0, add_differentiation = False, add_blp = False, 
	integration_options = {'type' : 'grid', 'size' : 9}):

	df['market_ids'] = df['dma_code'].astype(str) + '_' + df[month_or_quarter].astype(str)
	df = df.rename(columns = {'owner' : 'firm_ids'})

	# Baseline formulation
	num_chars = 2
	string_chars = '1 + prices'
	for this_char in chars:
		string_chars = string_chars + ' + ' this_char
		num_chars += 1
	formulation_char = pyblp.Formulation(string_chars, absorb = 'C(TIME) + C(dma_code)')
	formulation_fe = pyblp.Formulation('0 + prices', absorb = 'C(upc) + C(TIME) + C(dma_code)')

	# Add Gandhi-Houde or BLP instruments
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

	# Add the nests
	if nests is not None:
		if nests == 'inside':
			df['nesting_ids'] = 1
		else:
			df['nesting_ids'] = df[nests]

	return formulation_char, formulation_fe, df

def get_partial_f(df, chars):

	# First get the various characteristics and instruments
	endog_mat = df[['prices', 'shares']].to_numpy()
	characteristics_mat = df[chars].to_numpy()
	filter_col = [col for col in df if col.startswith('demand_instruments')]
	instruments_mat = df[filter_col].to_numpy()

	# Now generate the residualization
	fixed_effects = df['upc',TIME,'dma_code']
	alg = pyhdfe.create(fixed_effects, drop_singletons = False)
	endog_resid = alg.residualize(endog_mat)
	characteristics_resid = alg.residualize(characteristics_mat)
	characteristics_resid = sm.add_constant(characteristics_resid)
	instruments_resid = alg.residualize(instruments_mat)
	instruments_resid = np.concatenate((characteristics_resid, instruments_resid), axis = 1)

	# Compute the partial F and partial R^2
	piP_full = np.linalg.lstsq(instruments_resid, endog_resid)
	eP_full = endog_resid - instruments_resid @ piP_full
	sigmaP_full = (eP_full.T @ eP_full)

	piP_reduced = np.linalg.lstsq(characteristics_resid, endog_resid)
	eP_reduced = endog_resid - characteristics_resid @ piP_reduced
	sigmaP_reduced = (eP_reduced.T @ eP_reduced)

	partialF = ((sigmaP_reduced - sigmaP_full) @ np.linalg.inv(sigmaP_full)) * (characteristics_resid.shape[0] - instruments_resid.shape[1]) / (instruments_resid.shape[1] - characteristics_resid.shape[1]);
	partialR2 = (sigmaP_reduced - sigmaP_full) @ np.linalg.inv(sigmaP_reduced)

	partialF = np.diag(partialF)
	partialR2 = np.diag(partialR2)

	return partialF, partialR2


def estimate_demand(code, df, chars, nests = None, month_or_quarter = 'month', estimate_type = 'logit', 
	num_instruments = 0, add_differentiation = False, add_blp = False, use_knitro = True, 
	integration_options = {'type' : 'grid', 'size' : 9}, num_parallel = 1):

	# First get the formulations
	formulation_char, formulation_fe, df = create_formulation(code, df, chars, 
		nests = nests, month_or_quarter = month_or_quarter,	
		num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp, 
		integration_options = integration_options)

	# Get the first stage of instruments
	partialF, partialR2 = get_partial_f(df, chars)
	# PRINT THIS SOMEWHERE???

	# Set up optimization	
	if use_knitro:
		optimization = pyblp.Optimization('knitro', method_options = {'knitro_dir' : '/software/knitro/10.3'})
	else:
		optimization = pyblp.Optimization('l-bgfs-b')

	# Estimate
	if estimate_type == 'logit':

		problem_char = pyblp.Problem(formulation_char, df)
		problem_fe = pyblp.Problem(formulation_fe, df)

		if nests is not None:
			results_char = problem_char.solve()
			results_fe = problem_fe.solve()
		else:
			num_nests = len(df['nesting_ids'].unique())
			with pyblp.parallel(num_parallel):
				results_char = problem_char.solve(rho = 0.7 * np.ones((num_nests, 1)), optimization = optimization)
				results_fe = problem_fe.solve(rho = 0.7 * np.ones((num_nests, 1)), optimization = optimization)

		# Save as pickles
		dict_char = results_char.to_dict()
		dict_fe = results_fe.to_dict()

		pickle.dump(dict_char, open('m_' + code + '/output/logit_char_' + month_or_quarter + '.p', "wb"))
		pickle.dump(dict_fe, open('m_' + code + '/output/logit_fe_' + month_or_quarter + '.p', "wb"))


	elif estimate_type == 'blp':
		
		forumlation_blp = (formulation_fe, formulation_char)
		integration = pyblp.Integration(integration_options['type'], size = integration_options['size'])
		
		problem = pyblp.Problem(formulation_blp, df, integration = integration)
		with pyblp.parallel(num_parallel):
			results_blp = problem.solve(sigma = np.ones((num_chars, num_chars)), optimization = optimization)

		dict_blp = results_blp.to_dict()
		pickle.dump(dict_blp, open('m_' + code + '/output/blp_' + month_or_quarter + '.p', "wb"))

	else:
		# Can do this if we just want to run partial F
		print("Did not run estimation")

	

code = sys.argv[1]
month_or_quarter = sys.argv[2]
estimate_type = sys.argv[3]

df, characteristics, nest, num_instruments = gather_product_data(code)
estimate_demand(code, df, characteristics, nests = nest, month_or_quarter = month_or_quarter, estimate_type = estimate_type, 
	num_instruments = num_instruments)

