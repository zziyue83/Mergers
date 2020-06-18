import numpy as np
import pandas as pd
import pyblp
import matplotlib.pyplot as plt
import statsmodels.api as sm
import scipy.sparse as sp

# Read the Nevo data
data = pd.read_csv(pyblp.data.NEVO_PRODUCTS_LOCATION)
formulation = pyblp.Formulation('1 + prices')
uu = np.random.choice(data.market_ids.unique(), size = 70)
data_short = data[data['market_ids'].isin(uu)].copy()

problem_short = pyblp.Problem(formulation, data_short)
results_short = problem_short.solve()

# Run a silly simulation to check how simulation works
simulation_check = pyblp.Simulation(formulation, data_short, beta = results_short.beta, xi = results_short.xi)
simulation_results_check = simulation_check.replace_endogenous(costs = np.zeros((len(data_short), 1)), 
	prices = data_short.prices, 
	iteration = pyblp.Iteration(method = 'return'))
plt.scatter(data_short.shares, simulation_results_check.product_data.shares)

# Now get xi from results_short by product
data_short['xi'] = results_short.xi
product_xi = data_short[['product_ids', 'xi']].copy()
product_xi = product_xi.groupby('product_ids').mean()
product_xi_map = product_xi.to_dict()

# Now add that back to data
data_xi = data.product_ids.map(product_xi_map['xi'])
# data_xi[data.market_ids.isin(uu)] = results_short.xi # if you want to verify 
simulation = pyblp.Simulation(formulation, data, beta = results_short.beta, xi = data_xi)
simulation_results = simulation.replace_endogenous(costs = np.zeros((len(data), 1)), 
	prices = data.prices, 
	iteration = pyblp.Iteration(method = 'return'))
simulation_data = simulation_results.product_data

fig, axs = plt.subplots(3, figsize = (10, 15))
fig.suptitle('Model fit')
axs[0].scatter(data.shares[~data['market_ids'].isin(uu)], simulation_data.shares[~data['market_ids'].isin(uu)])
axs[0].set_title('Excluded markets')
axs[1].scatter(data.shares[data['market_ids'].isin(uu)], simulation_data.shares[data['market_ids'].isin(uu)])
axs[1].set_title('Included markets')

# Do David's version of estimating xi in two different ways
data_other = data[~data['market_ids'].isin(uu)].copy()
problem_other = pyblp.Problem(formulation, data_other)
results_other = problem_other.solve()
data_other['xi'] = results_other.xi
product_xi_other = data_other[['product_ids', 'xi']].copy()
product_xi_other = product_xi_other.groupby('product_ids').mean()
axs[2].scatter(1e16 * product_xi.xi, 1e16 * product_xi_other.xi)


excluded = sm.OLS(simulation_data.shares[~data['market_ids'].isin(uu)], sm.add_constant(data.shares[~data['market_ids'].isin(uu)])).fit()
excluded.summary()

included = sm.OLS(simulation_data.shares[data['market_ids'].isin(uu)], sm.add_constant(data.shares[data['market_ids'].isin(uu)])).fit()
included.summary()


##########################
# Try adding fixed effects
# Read the Nevo data
data = pd.read_csv(pyblp.data.NEVO_PRODUCTS_LOCATION)
data['nesting_ids'] = 1
formulation = pyblp.Formulation('0 + prices', absorb = 'C(product_ids) + C(market_ids)')
uu = np.random.choice(data.market_ids.unique(), size = 70)
data_short = data[data['market_ids'].isin(uu)].copy()

problem_short = pyblp.Problem(formulation, data_short)
results_short = problem_short.solve(rho = 0.7)
data_short['temp'] = results_short.delta - results_short.xi
data_short['fe'] = data_short['temp'] - results_short.beta[0, 0] * data_short['prices']

# Run a silly simulation to check how simulation works
# just_fe = data_short[['product_ids', 'fe']].copy().groupby('product_ids').mean().to_dict()
new_formulation = pyblp.Formulation('0 + prices + fe')
simulation_check = pyblp.Simulation(new_formulation, data_short, beta = np.append(results_short.beta, [1]), xi = results_short.xi, rho = results_short.rho)
simulation_results_check = simulation_check.replace_endogenous(costs = np.zeros((len(data_short), 1)), 
	prices = data_short.prices, 
	iteration = pyblp.Iteration(method = 'return'))
plt.scatter(data_short.shares, simulation_results_check.product_data.shares)

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