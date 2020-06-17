import numpy as np
import pandas as pd
import pyblp
import matplotlib.pyplot as plt

# Read the Nevo data
data = pd.read_csv(pyblp.data.NEVO_PRODUCTS_LOCATION)
formulation = pyblp.Formulation('1 + prices + sugar + mushy')
uu = np.random.choice(data.market_ids.unique(), size = 70)
data_short = data[data['market_ids'].isin(uu)].copy()

problem_short = pyblp.Problem(formulation, data_short)
results_short = problem_short.solve()

# Now get xi from results_short by product
data_short['xi'] = results_short.xi
product_xi = data_short[['product_ids', 'xi']].copy()
product_xi = product_xi.groupby('product_ids').mean()
product_xi_map = product_xi.to_dict()

# Now add that back to data
data_xi = data.product_ids.map(product_xi_map['xi'])
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