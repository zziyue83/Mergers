import numpy as np
import pandas as pd
import pyblp
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.sparse import csr_matrix

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
formulation = pyblp.Formulation('0 + prices', absorb = 'C(product_ids)')
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

def recover_fixed_effects(fe_columns, fe_vals):
	# If there's only one FE, then this is easy
	if len(fe_columns.columns) == 1:
		do something easy 
	else:
		# First get the FEs
		fe_dict = {}
		num_fe = []
		for col in fe_columns.columns:
			this_unique_fe = fe_columns[col].unique()
			num_fe.append(len(this_unique_fe))
			fe_dict[col] = unique_fe

		num_rows = len(fe_columns)
		num_cols = sum(num_fe) - (len(num_fe) - 1)

		# First build the csr_matrix
		start = 0
		indptr = np.array([0])
		indices = np.array([])
		for row in fe_columns.iterrows():
			for col in fe_columns.columns:
				this_fe = fe_columns.loc[row, col]
				GET INDEX IN fe_dict[col]

				col_number = XXX?
				indices = np.append(indices, col_number)
				start += 1
			indptr = np.append(indptr, start)
		data = np.ones(???)
		fe_matrix = csr_matrix((data, indices, indptr), shape=(num_rows, num_cols))

		inverse!!! (fe_matrix.transpose() TIMES fe_matrix)
		fe_matrix.transpose().dot(fe_vals) 

	return something