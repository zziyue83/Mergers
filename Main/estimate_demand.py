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
import scipy.sparse as sp

# Set pyblp options
pyblp.options.digits = 3
pyblp.options.verbose = True
pyblp.options.flush_output = True

def recover_fixed_effects(fe_columns, fe_vals, omit_constant = True):
	# If there's only one FE, then this is easy
	return_dict = {}

	if len(fe_columns.columns) == 1:
		colname = fe_columns.columns[0]
		fe_columns['fe_value'] = fe_vals
		fe_columns = fe_columns.groupby(colname).mean()
		return_dict[colname] = fe_columns.to_dict()
	else:
		# First get the FEs -- need to drop one element
		fe_dict = {}
		start_col_number = {}
		end_col_number = {}
		start_col = 0
		first_col = True
		removed_fe = {}
		for col in fe_columns.columns:
			this_unique_fe = fe_columns[col].unique().tolist()
			if first_col and omit_constant:
				removed_fe[col] = None
				first_col = False
			else:
				removed_fe[col] = this_unique_fe.pop(0)
			start_col_number[col] = start_col 
			start_col += len(this_unique_fe)
			end_col_number[col] = start_col
			fe_dict[col] = this_unique_fe

		num_rows = len(fe_columns)
		num_cols = start_col

		# First build the csr_matrix
		start = 0
		indptr = np.array([0])
		indices = np.array([])
		for index, row in fe_columns.iterrows():
			for col in fe_columns.columns:
				this_fe = row[col]
				try:
					this_index = fe_dict[col].index(this_fe)
				except ValueError:
					# Omitted value
					print('Omitted value for ' + col)
					continue

				col_number = start_col_number[col] + this_index
				indices = np.append(indices, col_number)
				start += 1
			indptr = np.append(indptr, start)
		fe_matrix = sp.csr_matrix((np.ones_like(indices), indices, indptr), shape=(num_rows, num_cols))

		output = sp.linalg.lsqr(fe_matrix, fe_vals)
		indiv_fe_vals = output[0]

		# Now go through and map indices pack to values
		# Return a dictionary of dictionaries
		for col in fe_columns.columns:
			df = pd.DataFrame({col : fe_dict[col], 'fe_value' : indiv_fe_vals[start_col_number[col]:end_col_number[col]]})
			if removed_fe[col] is not None:
				df = df.append({col : removed_fe[col], 'fe_value' : 0}, ignore_index = True)
			df = df.set_index(col)
			return_dict[col] = df.to_dict()

	return return_dict

def add_characteristics(code, df, char_map, chars):
	for this_char in chars:
		df[this_char] = df['upc'].map(char_map[this_char])
	return df

def add_instruments(code, df, instrument_names):

	add_differentiation = False
	if 'differentiation' in instrument_names:
		add_differentiation = True
		instrument_names.remove('differentiation')

	add_blp = False
	if 'blp' in instrument_names:
		add_blp = True
		instrument_names.remove('blp')

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

	return df, i, add_differentiation, add_blp

def gather_product_data(code, month_or_quarter = 'month'):
	info_dict = aux.parse_info(code)
	characteristics = aux.get_characteristics(info_dict["Characteristics"])
	nest = aux.get_nest(info_dict["Nest"])
	instrument_names = aux.get_instruments(info_dict["Instruments"])

	to_append = characteristics
	if (nest is not None) and (nest not in characteristics):
		to_append.append(nest)

	# Get the characteristics map
	char_df = pd.read_csv('m_' + code + '/properties/characteristics.csv', delimiter = ',', index_col = 'upc')
	char_map = char_df.to_dict()

	df = pd.read_csv('m_' + code + '/intermediate/data_' + month_or_quarter + '.csv', delimiter = ',')
	df = aux.append_owners(code, df)
	df = add_characteristics(code, cf, char_map, to_append)
	df, num_instruments = add_instruments(code, df, instrument_names)

	return df, characteristics, nest, num_instruments, add_differentiation, add_blp

def create_formulation(code, df, chars, nests = None, month_or_quarter = 'month',
	num_instruments = 0, add_differentiation = False, add_blp = False):

	df['market_ids'] = df['dma_code'].astype(str) + '_' + df[month_or_quarter].astype(str)
	df = df.rename(columns = {'owner' : 'firm_ids'})

	# Baseline formulation
	num_chars = 2
	string_chars = '1 + prices'
	for this_char in chars:
		string_chars = string_chars + ' + ' this_char
		num_chars += 1
	formulation_char = pyblp.Formulation(string_chars, absorb = 'C(dma_code) + C(' + month_or_quarter + ')') # These are seasonality FEs
	formulation_fe = pyblp.Formulation('0 + prices', absorb = 'C(upc) + C(dma_code) + C(' + month_or_quarter + ')')

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

def write_to_file(problem, code, filepath):

	# FIGURE THIS OUT!!!

	# Save as pickles
	with open('m_' + code + '/output/logit_char_' + month_or_quarter + '.p', 'wb') as fout:
		pickle.dump(results_char.to_dict(), fout)
	with open('m_' + code + '/output/logit_fe_' + month_or_quarter + '.p', 'wb') as fout:
		pickle.dump(results_char.to_dict(), fout)

	with open('m_' + code + '/output/blp_' + month_or_quarter + '.p', 'wb') as fout:
			pickle.dump(results_blp.to_dict(), fout)


def estimate_demand(code, df, chars = None, nests = None, month_or_quarter = 'month', estimate_type = 'logit', 
	num_instruments = 0, add_differentiation = False, add_blp = False, use_knitro = True, 
	integration_options = {'type' : 'grid', 'size' : 9}, num_parallel = 1):

	# First get the formulations
	formulation_char, formulation_fe, df = create_formulation(code, df, chars, 
		nests = nests, month_or_quarter = month_or_quarter,	
		num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp)

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

		return [results_char, results_fe]

	elif estimate_type == 'blp':
		
		forumlation_blp = (formulation_fe, formulation_char)
		integration = pyblp.Integration(integration_options['type'], size = integration_options['size'])
		
		problem = pyblp.Problem(formulation_blp, df, integration = integration)
		with pyblp.parallel(num_parallel):
			results_blp = problem.solve(sigma = np.ones((num_chars, num_chars)), optimization = optimization)

		return results_blp

	else:
		# Can do this if we just want to run partial F
		print("Did not run estimation")

def crossvalidate_demand(code, df, cutoff_date = None, timespan = 'pre', chars = None, nests = None, 
	month_or_quarter = 'month', estimate_type = 'logit', 
	num_instruments = 0, add_differentiation = False, add_blp = False, use_knitro = True, 
	integration_options = {'type' : 'grid', 'size' : 9}, num_parallel = 1):
	
	# First subset the df if needed
	if cutoff_date is not None:
		dt = datetime.strptime(cutoff_date, '%Y-%m-%d')
		if month_or_quarter == 'month':
			dt_month_or_quarter = dt.month 
		else:
			dt_month_or_quarter = ceil(dt.month / 3)

		if timespan == 'pre':
			df = df[df['year'] < dt.year | df['year'] == dt.year & df[month_or_quarter] < dt_month_or_quarter]
		elif timespan == 'post':
			df = df[df['year'] > dt.year | df['year'] == dt.year & df[month_or_quarter] > dt_month_or_quarter]

	# Now choose the markets
	unique_dmas = df['dma_code'].unique()
	dma_group1 = np.random.choice(unique_dmas, size = ceil(0.5 * len(unique_dmas)), replace = False)
	dma_group2 = list(set(unique_dmas) - set(dma_group1))

	df['time'] = 100 * df['year'] + df[month_or_quarter]
	unique_times = df['time'].unique()
	time_group1 = np.random.choice(unique_times, size = ceil(0.5 * len(unique_times)), replace = False)
	time_group2 = list(set(unique_times) - set(time_group1))

	inside_group = (df['dma_code'].isin(dma_group1) & df['time'].isin(time_group1)) | (df['dma_code'].isin(dma_group2) & df['time'].isin(time_group2)) 
	df_short = df[inside_group].copy()

	results_short = estimate_demand(code, df_short, chars = characteristics, nests = nest, month_or_quarter = month_or_quarter, 
		estimate_type = estimate_type, num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp)

	# Now get the fixed effects
	df_short['temp'] = results_short.delta - results_short.xi
	df_short['fe'] = data_short['temp'] - results_short.beta[0, 0] * df_short['prices'] # GENERALIZE THIS!!!
	df = df.drop('temp', axis = 1)

	fe_levels = ['upc', 'dma_code', month_or_quarter]
	fe_dict = recover_fixed_effects(df[fe_levels], df['fe'])
	
	df['fe'] = 0
	for fe in fe_levels:
		df['fe'] = df['fe'] + df[fe].map(fe_dict[fe]['fe_value'])

	# Now get xi
	df['xi'] = something

	# Generate the simulation
	new_formulation = pyblp.Formulation('0 + prices + fe')	
	simulation = pyblp.Simulation(new_formulation, df, 
		beta = np.append(results_short.beta, [1]),
		xi = df.xi,
		rho = results_short.rho)
	simulation_results = simulation.replace_endogenous(costs = np.zeros((len(df), 1)),
		prices = df.prices,
		iteration = pyblp.Iteration(method = 'return'))

	# Now get the inside and outside shares
	inside_shares_actual = df.shares[inside_group]
	outside_shares_actual = df.shares[~inside_group]
	inside_shares_predicted = simulation_results.product_data.shares[inside_group]
	outside_shares_predicted = simulation_results.product_data.shares[~inside_group]
	
code = sys.argv[1]
month_or_quarter = sys.argv[2]
estimate_type = sys.argv[3]

df, characteristics, nest, num_instruments, add_differentiation, add_blp = gather_product_data(code, month_or_quarter)
estimate_demand(code, df, chars = characteristics, nests = nest, month_or_quarter = month_or_quarter, estimate_type = estimate_type, 
	num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp)

