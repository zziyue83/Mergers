# -*- coding: utf-8 -*-
import pyblp
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Set options
pyblp.options.digits = 3
pyblp.options.verbose = False
pyblp.__version__

# Load data
product_data = pd.read_csv(pyblp.data.NEVO_PRODUCTS_LOCATION)
product_data.head()

# Get the formulations
linear_formulation = pyblp.Formulation('0 + prices', absorb = 'C(product_ids)')
nonlinear_formulation = pyblp.Formulation('1 + prices + sugar + mushy')
product_formulations = (linear_formulation, nonlinear_formulation)

# Set the optimizer
# -- In general, we will want to use Knitro, in which case replace 'bfgs' by 'knitro'
bfgs = pyblp.Optimization('bfgs', {'gtol' : 1e-10})

# Set the integration routine and run the optimization
mc_integration = pyblp.Integration('monte_carlo', size = 50, seed = 0)
mc_problem = pyblp.Problem(product_formulations, 
                           product_data, 
                           integration = mc_integration)
mc_results = mc_problem.solve(sigma = np.ones((4, 4)), optimization = bfgs)

# pr_integration = pyblp.Integration('product', size = 5)
# pr_problem = pyblp.Problem(product_formulations, product_data, integration = pr_integration)
# pr_results = pr_problem.solve(sigma = np.ones((4, 4)), optimization = bfgs)

# How to run a merger
costs = mc_results.compute_costs()
plt.hist(costs, bins = 50)
product_data['merger_ids'] = product_data['firm_ids'].replace(2, 1) # this is what you edit based on the config file
changed_prices = mc_results.compute_prices(firm_ids = product_data['merger_ids'], 
                                           costs = costs)