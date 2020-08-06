from linearmodels.iv import IV2SLS
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
#import knitro

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

def add_instruments(code, df, instrument_names, month_or_quarter):

	add_differentiation = False
	if 'differentiation' in instrument_names:
		add_differentiation = True
		instrument_names.remove('differentiation')

	add_blp = False
	if 'blp' in instrument_names:
		add_blp = True
		instrument_names.remove('blp')

	if 'distance-diesel' in instrument_names:
		# First get the distances and merge with df
		distances = pd.read_csv('../../../All/m_' + code + '/intermediate/distances.csv', delimiter = ',', index_col = ['brand_code_uc', 'owner', 'dma_code'])
		df = df.join(distances, on = ['brand_code_uc', 'owner', 'dma_code'], how = 'left')

		# Next, get the diesel prices and merge with df
		diesel_data = pd.read_csv('../../../All/instruments/diesel.csv', delimiter = ',')
		diesel_data['date'] = pd.to_datetime(diesel_data['date'])
		diesel_data['year'] = diesel_data['date'].dt.year

		if month_or_quarter == 'month':
			diesel_data[month_or_quarter] = diesel_data['date'].dt.month
		elif month_or_quarter == 'quarter':
			diesel_data[month_or_quarter] = np.ceil(diesel_data['date'].dt.month/3)

		diesel_data_period = diesel_data.groupby([month_or_quarter, 'year'])['value'].agg('mean')

		df = df.join(diesel_data_period, on = [month_or_quarter, 'year'], how = 'left')
		df.rename(columns={'value': 'diesel'}, inplace=True)

		# Then get diesel prices to multiply
		df['demand_instruments0'] = df['distance'] * df['diesel']
		df = df.drop(['distance', 'diesel'], axis=1)

		instrument_names.remove('distance-diesel')
		i = 1

	else:
		i = 0

	# Then get the remaining instruments
	for instrument in instrument_names:
		inst_data = pd.read_csv('../../../All/instruments/' + instrument + '.csv', delimiter = ',')
		inst_data['date'] = pd.to_datetime(inst_data['date'])
		inst_data['year'] = inst_data['date'].dt.year

		if month_or_quarter == 'month':
			inst_data[month_or_quarter] = inst_data['date'].dt.month
		elif month_or_quarter == 'quarter':
			inst_data[month_or_quarter] = np.ceil(inst_data['date'].dt.month/3)

		inst_data_period = inst_data.groupby([month_or_quarter, 'year'])['value'].agg('mean')

		df = df.join(inst_data_period, on = [month_or_quarter, 'year'], how = 'left')
		df.rename(columns={'value': 'demand_instruments' + str(i)}, inplace=True)
		i += 1

	return df, i, add_differentiation, add_blp

def gather_product_data(code, month_or_quarter = 'month'):
	info_dict = aux.parse_info(code)
	characteristics_ls = aux.get_insts_or_chars_or_nests(info_dict["Characteristics"])
	nest = aux.get_insts_or_chars_or_nests(info_dict["Nest"])
	instrument_ls = aux.get_insts_or_chars_or_nests(info_dict["Instruments"])

	to_append = characteristics_ls
	if (nest is not None) and (nest not in characteristics_ls) and (nest != 'inside'):
		to_append.append(nest)

	# Get the characteristics map
	char_df = pd.read_csv('../../../All/m_' + code + '/properties/characteristics.csv', delimiter = ',', index_col = 'upc')
	char_map = char_df.to_dict()

	df = pd.read_csv('../../../All/m_' + code + '/intermediate/data_' + month_or_quarter + '.csv', delimiter = ',')
	print(df.shape)
	df = aux.append_owners(code, df, month_or_quarter)
	print(df.shape)
	df = add_characteristics(code, df, char_map, to_append)
	print(df.shape)
	df, num_instruments, add_differentiation, add_blp = add_instruments(code, df, instrument_ls, month_or_quarter)

	return df, characteristics_ls, nest, num_instruments, add_differentiation, add_blp	

def create_formulation(code, df, chars, nests = None, month_or_quarter = 'month',
	num_instruments = 0, add_differentiation = False, add_blp = False):

	df['market_ids'] = df['dma_code'].astype(str) +  '_' + df['year'].astype(str) + '_' + df[month_or_quarter].astype(str)
	df = df.rename(columns = {'owner' : 'firm_ids'})

	# Baseline formulation
	num_chars = 2
	string_chars = '0 + prices'
	for this_char in chars:
		string_chars = string_chars + ' + ' + this_char
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

	return formulation_char, formulation_fe, df, num_chars

def get_partial_f(df, chars, nests, month_or_quarter):

	# Get endogenous variables (if nests, compute within-nest share)
	if nests is not None:
		df['total_nest_shares'] = df.groupby(['market_ids','nesting_ids'])['shares'].transform('sum')
		df['log_within_nest_shares'] = np.log(df['shares']/df['total_nest_shares'])
		endog_mat = df[['prices', 'shares', 'log_within_nest_shares']].to_numpy()
	else:
		endog_mat = df[['prices', 'shares']].to_numpy()

	# First get the various characteristics and instruments
	characteristics_mat = df[chars].to_numpy()
	filter_col = [col for col in df if col.startswith('demand_instruments')]
	instruments_mat = df[filter_col].to_numpy()

	# Now generate the residualization
	fixed_effects = df[['upc',month_or_quarter,'dma_code']]
	alg = pyhdfe.create(fixed_effects, drop_singletons = False)
	endog_resid = alg.residualize(endog_mat)
	characteristics_resid = alg.residualize(characteristics_mat)
	characteristics_resid = sm.add_constant(characteristics_resid)
	instruments_resid = alg.residualize(instruments_mat)
	instruments_resid = np.concatenate((characteristics_resid, instruments_resid), axis = 1)

	# Compute the partial F and partial R^2
	piP_full = np.linalg.lstsq(instruments_resid, endog_resid)[0]
	eP_full = endog_resid - instruments_resid @ piP_full
	sigmaP_full = (eP_full.T @ eP_full)

	piP_reduced = np.linalg.lstsq(characteristics_resid, endog_resid)[0]
	eP_reduced = endog_resid - characteristics_resid @ piP_reduced
	sigmaP_reduced = (eP_reduced.T @ eP_reduced)

	partialF = ((sigmaP_reduced - sigmaP_full) @ np.linalg.inv(sigmaP_full)) * (characteristics_resid.shape[0] - instruments_resid.shape[1]) / (instruments_resid.shape[1] - characteristics_resid.shape[1])
	partialR2 = (sigmaP_reduced - sigmaP_full) @ np.linalg.inv(sigmaP_reduced)

	partialF = np.diag(partialF)
	partialR2 = np.diag(partialR2)

	return partialF, partialR2

def write_to_file(results, code, filepath):
	# Save as pickle
	with open('../../../All/m_' + code + '/output/' + filepath + '.p', 'wb') as fout:
		pickle.dump(results.to_dict(), fout)



def estimate_demand(code, df, chars = None, nests = None, month_or_quarter = 'month', estimate_type = 'logit', linear_fe = False,
	num_instruments = 0, add_differentiation = False, add_blp = False, use_knitro = False,
	integration_options = {'type' : 'grid', 'size' : 9}, num_parallel = 1):

	# First get the formulations
	formulation_char, formulation_fe, df, num_chars = create_formulation(code, df, chars,
		nests = nests, month_or_quarter = month_or_quarter,
		num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp)

	# Set up optimization
	if use_knitro:
		optimization = pyblp.Optimization('knitro', method_options = {'knitro_dir' : '/software/knitro/10.3'})
	else:
		optimization = pyblp.Optimization('l-bfgs-b')

	# Estimate logit - nested logit
	if estimate_type == 'logit':


		#upc fixed-effects specs
		if linear_fe:

			# set up variables
			characteristics_mat = df[chars].to_numpy()
			filter_col = [col for col in df if col.startswith('demand_instruments')]
			instruments_mat = df[filter_col].to_numpy()

			# Initialize demeaning algorithm and demean variables (upc dma - FE).
			fixed_effects = df[['upc', 'dma_code']] #loosen FE for now
			alg = pyhdfe.create(fixed_effects, drop_singletons = False)
			instruments_resid = alg.residualize(instruments_mat)

			#nested logit
			if nests is not None:

				df['outside_share'] = 1 - df.groupby(['market_ids'])['shares'].transform('sum')
				df['total_nest_shares'] = df.groupby(['market_ids','nesting_ids'])['shares'].transform('sum')
				df['within_nest_shares'] = df['shares']/df['total_nest_shares']
				df['log_within_nest_shares'] = np.log(df['within_nest_shares'])
				df['logsj_logs0'] = np.log(df['shares']) - np.log(df['outside_share']) #our RHS variable

				endog_mat = df[['prices', 'logsj_logs0', 'log_within_nest_shares']].to_numpy()
				endog_resid = alg.residualize(endog_mat)

				df['logsj_logs0_resid'] = endog_resid[:, [1]] #RHS residualized
				df['prices_resid'] = endog_resid[:, [0]]
				df['log_within_nest_shares_resid'] = endog_resid[:, [2]]

				month_or_quarter = df[month_or_quarter]
				dependent = df['logsj_logs0_resid']
				endogenous = df[['prices_resid', 'log_within_nest_shares_resid']]

				results = IV2SLS(dependent=dependent, exog=month_or_quarter, endog=endogenous, instruments=instruments_resid).fit(cov_type='robust')

				prices_param = results.params['prices_resid']
				log_within_nest_shares_param = results.params['log_within_nest_shares_resid']
				shares_mat = df[['within_nest_shares', 'shares']].to_numpy()
				shares_resid = alg.residualize(shares_mat)
				df['within_nest_shares_resid'] = endog_resid[:, [0]]
				df['shares_resid'] = endog_resid[:, [1]]
				own_price_elasticity = -(prices_param * df['prices_resid'])*(1/(1-log_within_nest_shares_param)-(log_within_nest_shares_param/(1-log_within_nest_shares_param) * df['within_nest_shares_resid'])-df['shares_resid'])


			#logit
			else:

				endog_mat = df[['prices', 'logsj_logs0']].to_numpy()
				endog_resid = alg.residualize(endog_mat)

				df['logsj_logs0_resid'] = endog_resid[:, [1]]
				df['prices_resid'] = endog_resid[:, [0]]

				month_or_quarter = df[month_or_quarter]
				dependent = df['logsj_logs0_resid']
				endogenous = df['prices_resid']

				results = IV2SLS(dependent=dependent, exog=month_or_quarter, endog=endogenous, instruments=instruments_resid).fit(cov_type='robust')


		#characteristics specs
		else:

			# set up variables
			characteristics_mat = df[chars].to_numpy()
			filter_col = [col for col in df if col.startswith('demand_instruments')]
			instruments_mat = df[filter_col].to_numpy()

			# Initialize demeaning algorithm and demean variables (dma time - FE).
			fixed_effects = df[[month_or_quarter, 'dma_code']] #no upc FE here
			alg = pyhdfe.create(fixed_effects, drop_singletons = False)
			characteristics_resid = alg.residualize(characteristics_mat)
			characteristics_resid = sm.add_constant(characteristics_resid)
			instruments_resid = alg.residualize(instruments_mat)

			#nested logit
			if nests is not None:

				df['outside_share'] = 1 - df.groupby(['market_ids'])['shares'].transform('sum')
				df['total_nest_shares'] = df.groupby(['market_ids','nesting_ids'])['shares'].transform('sum')
				df['log_within_nest_shares'] = np.log(df['shares']/df['total_nest_shares'])
				df['logsj_logs0'] = np.log(df['shares']) - np.log(df['outside_share']) #our RHS variable

				endog_mat = df[['prices', 'logsj_logs0', 'log_within_nest_shares']].to_numpy()
				endog_resid = alg.residualize(endog_mat)

				#Regress endog_resid on instruments_resid
				df['logsj_logs0_resid'] = endog_resid[:, [1]]
				df['prices_resid'] = endog_resid[:, [0]]
				df['log_within_nest_shares_resid'] = endog_resid[:, [2]]

				dependent = df['logsj_logs0_resid']
				endogenous = df[['prices_resid', 'log_within_nest_shares_resid']]

				results = IV2SLS(dependent=dependent, exog=characteristics_resid, endog=endogenous, instruments=instruments_resid).fit(cov_type='robust')

				prices_param = results.params['prices_resid']
				log_within_nest_shares_param = results.params['log_within_nest_shares_resid']
				shares_mat = df[['within_nest_shares', 'shares']].to_numpy()
				shares_resid = alg.residualize(shares_mat)
				df['within_nest_shares_resid'] = endog_resid[:, [0]]
				df['shares_resid'] = endog_resid[:, [1]]
				own_price_elasticity = -(prices_param * df['prices_resid'])*(1/(1-log_within_nest_shares_param)-(log_within_nest_shares_param/(1-log_within_nest_shares_param) * df['within_nest_shares_resid'])-df['shares_resid'])


			#logit
			else:

				endog_mat = df[['prices', 'logsj_logs0']].to_numpy()
				endog_resid = alg.residualize(endog_mat)

				df['logsj_logs0_resid'] = endog_resid[:, [1]]
				df['prices_resid'] = endog_resid[:, [0]]

				dependent = df['logsj_logs0_resid']
				endogenous = df['prices_resid']

				results = IV2SLS(dependent=dependent, exog=characteristics_resid, endog=endogenous, instruments=instruments_resid).fit(cov_type='robust')

		se_adjusted = np.sqrt(np.square(results.std_errors) * results.df_resid / (results.df_resid - alg.degrees)) #dof adjustments
		print(se_adjusted)

		return results


	elif estimate_type == 'blp':

		forumlation_blp = (formulation_fe, formulation_char)
		integration = pyblp.Integration(integration_options['type'], size = integration_options['size'])

		problem = pyblp.Problem(formulation_blp, df, integration = integration)
		with pyblp.parallel(num_parallel):
			if nests is None:
				results = problem.solve(sigma = np.ones((num_chars, num_chars)), optimization = optimization)
			else:
				num_nests = len(df['nesting_ids'].unique())
				results = problem.solve(sigma = np.ones((num_chars, num_chars)), rho = 0.7 * np.ones((num_nests, 1)), optimization = optimization)

		return results

	elif estimate_type == 'partialF':
		print("Did not run estimation")

		# Get the first stage of instruments
		partialF, partialR2 = get_partial_f(df, chars, nests, month_or_quarter)
		print(partialF)
		print(partialR2)
		return None
	else:
		return None



code = sys.argv[1]
month_or_quarter = sys.argv[2]
estimate_type = sys.argv[3]

#log_out = open('../../../All/m_' + code + '/output/estimate_demand.log', 'w')
#log_err = open('../../../All/m_' + code + '/output/estimate_demand.err', 'w')
#sys.stdout = log_out
#sys.stderr = log_err

df, characteristics_ls, nest, num_instruments, add_differentiation, add_blp = gather_product_data(code, month_or_quarter)
print(df.shape)
estimate_demand(code, df, chars = characteristics_ls, nests = nest, month_or_quarter = month_or_quarter, estimate_type = estimate_type,
	num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp, linear_fe = False)

#log_out.close()
#log_err.close()