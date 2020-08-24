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
import subprocess
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import inv

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



	use_stata = True
	if use_stata:
		data.to_csv('../../../All/m_' + code + '/intermediate/stata_did_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8', index = False)


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

		for ch in chars:

			df = df.rename(columns={ch: 'char'+ch})

		#upc fixed-effects specs
		if linear_fe:

			spec = "Linear_FE"

			# set up variables
			filter_col = [col for col in df if col.startswith('demand_instruments')]

			#nested logit
			if nests is not None:

				routine = "Nested_Logit"

				df['outside_share'] = 1 - df.groupby(['market_ids'])['shares'].transform('sum')
				df['total_nest_shares'] = df.groupby(['market_ids','nesting_ids'])['shares'].transform('sum')
				df['within_nest_shares'] = df['shares']/df['total_nest_shares']
				df['log_within_nest_shares'] = np.log(df['within_nest_shares'])
				df['logsj_logs0'] = np.log(df['shares']) - np.log(df['outside_share']) #our RHS variable

				df.to_csv('../../../All/m_' + code + '/intermediate/demand_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8', index = False)
				print(df.loc[0])

				dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/Nested_Logit.do"
				DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
				path_input = "../../../All/m_" + code + "/intermediate"
				path_output = "../output/"
				cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, month_or_quarter, routine, spec] #check *args to pass to stata
				subprocess.call(cmd)

				#recover alpha and rho
				file = open('../../../All/m_' + code + '/output/demand_results_' + month_or_quarter + '.txt', mode = 'r')
				stata_output = file.read()
				file.close()
				prices_param = float(re.findall('prices\\\t(.*?)\*\*\*', stata_output, re.DOTALL)[0])
				log_within_nest_shares_param = float(re.findall('log_within_nest_shares\\\t(.*?)\*\*\*', stata_output, re.DOTALL)[0])
				own_price_elasticity = -(prices_param * df['prices'])*(1/(1-log_within_nest_shares_param)-(log_within_nest_shares_param/(1-log_within_nest_shares_param) * df['within_nest_shares'])-df['shares'])
				print(own_price_elasticity)

				#marginal costs
				#dD_inv = ()
				dD = ()
				for market in df['market_ids'].unique():
					df_market = df[df['market_ids']==market]
					J = df_market.shape[0]
					dD_block = csr_matrix((J, J), dtype=int)
					for i in range(J):
						for k in range(J):
							upc_i = df_market.iloc[i]
							upc_k = df_market.iloc[k]
							if (upc_i['firm_ids'] == upc_k['firm_ids']) & (i > k):
								if (upc_i['nesting_ids'] == upc_k['nesting_ids']):
									dD_block[i, k] = prices_param * upc_k['shares'] * ((log_within_nest_shares_param/(1-log_within_nest_shares_param))*upc_i['within_nest_shares']+upc_i['shares'])
								else:
									dD_block[i, k] = prices_param * upc_i['shares'] * upc_k['shares']
							elif i == k:
								dD_block[i, k] = own_price_elasticity[i] * (upc_i['shares']/upc_i['prices'])
							elif (upc_i['firm_ids'] == upc_k['firm_ids']) & (i < k):
								if (upc_i['nesting_ids'] == upc_k['nesting_ids']):
									dD_block[i, k] = prices_param * upc_k['shares'] * ((log_within_nest_shares_param/(1-log_within_nest_shares_param))*upc_i['within_nest_shares']+upc_i['shares'])
								else:
									dD_block[i, k] = dD_block[k, i]
							else:
								dD_block[i, k] = 0
					#dD_block_inv = inv(dD_block)
					#print(dD_block_inv)
					#dD_inv = dD_inv + (dD_block_inv,)
					#print(dD_inv)
					dD = dD + (dD_block, )

				#dD_inv_diag = block_diag(dD_inv)
				#df['mg_costs'] = df['prices']+csr_matrix.dot(df['shares'], dD_inv_diag)
				assert np.linalg.matrix_rank(dD) == dD.shape[1], "Not full rank"
				df['mg_costs'] = df['prices']+csr_matrix.dot(df['shares'], inv(dD)) # haven't changed yet
				print(df)

			#logit
			else:

				routine = "Logit"

				df['logsj_logs0'] = np.log(df['shares']) - np.log(df['outside_share']) #our RHS variable

				df.to_csv('../../../All/m_' + code + '/intermediate/demand_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8', index = False)

				dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/Nested_Logit.do"
				DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
				path_input = "../../../All/m_" + code + "/intermediate"
				path_output = "../output/"
				cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, month_or_quarter, routine, spec] #check *args to pass to stata
				subprocess.call(cmd)
				
				#recover alpha and rho
				file = open('../../../All/m_' + code + '/info.txt', mode = 'r')
				stata_output = file.read()
				file.close()
				prices_param = float(re.findall('prices\\\t(.*?)\*\*\*', stata_output, re.DOTALL)[0])
				own_price_elasticity = -(prices_param * df['prices'])*(1-df['shares'])


		#characteristics specs
		else:

			spec = "Chars"

			# set up variables
			filter_col = [col for col in df if col.startswith('demand_instruments')]


			#nested logit
			if nests is not None:

				df['outside_share'] = 1 - df.groupby(['market_ids'])['shares'].transform('sum')
				df['total_nest_shares'] = df.groupby(['market_ids','nesting_ids'])['shares'].transform('sum')
				df['within_nest_shares'] = df['shares']/df['total_nest_shares']
				df['log_within_nest_shares'] = np.log(df['within_nest_shares'])
				df['logsj_logs0'] = np.log(df['shares']) - np.log(df['outside_share']) #our RHS variable

				df.to_csv('../../../All/m_' + code + '/intermediate/demand_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8', index = False)

				dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/Nested_Logit.do"
				DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
				path_input = "../../../All/m_" + code + "/intermediate"
				path_output = "../output/"
				cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, month_or_quarter, routine, spec] #check *args to pass to stata
				subprocess.call(cmd)

				#recover alpha and rho
				file = open('../../../All/m_' + code + '/info.txt', mode = 'r')
				stata_output = file.read()
				file.close()
				prices_param = float(re.findall('prices\\\t(.*?)\*\*\*', stata_output, re.DOTALL)[0])
				log_within_nest_shares_param = float(re.findall('log_within_nest_shares\\\t(.*?)\*\*\*', stata_output, re.DOTALL)[0])
				own_price_elasticity = -(prices_param * df['prices'])*(1/(1-log_within_nest_shares_param)-(log_within_nest_shares_param/(1-log_within_nest_shares_param) * df['within_nest_shares'])-df['shares'])

			#logit
			else:

				routine = "Logit"

				df['logsj_logs0'] = np.log(df['shares']) - np.log(df['outside_share']) #our RHS variable

				df.to_csv('../../../All/m_' + code + '/intermediate/demand_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8', index = False)

				dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/Nested_Logit.do"
				DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
				path_input = "../../../All/m_" + code + "/intermediate"
				path_output = "../output/"
				cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, month_or_quarter, routine, spec] #check *args to pass to stata
				subprocess.call(cmd)

				#recover alpha and rho
				file = open('../../../All/m_' + code + '/info.txt', mode = 'r')
				stata_output = file.read()
				file.close()
				prices_param = float(re.findall('prices\\\t(.*?)\*\*\*', stata_output, re.DOTALL)[0])
				own_price_elasticity = -(prices_param * df['prices'])*(1-df['shares'])


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
linear_fe = sys.argv[4]

log_out = open('../../../All/m_' + code + '/output/estimate_demand.log', 'w')
log_err = open('../../../All/m_' + code + '/output/estimate_demand.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

df, characteristics_ls, nest, num_instruments, add_differentiation, add_blp = gather_product_data(code, month_or_quarter)
print(df.shape)
estimate_demand(code, df, chars = characteristics_ls, nests = nest, month_or_quarter = month_or_quarter, estimate_type = estimate_type,
	num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp, linear_fe = linear_fe)

log_out.close()
log_err.close()

