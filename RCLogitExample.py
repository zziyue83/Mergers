import pyblp
import numpy as np
import pandas as pd

pyblp.options.digits = 2
pyblp.options.verbose = False

product_data = pd.read_csv(pyblp.data.NEVO_PRODUCTS_LOCATION)
print(product_data.head())

X1_formulation = pyblp.Formulation('0 + prices', absorb='C(product_ids)')
X2_formulation = pyblp.Formulation('1 + prices + sugar + mushy')
product_formulations = (X1_formulation, X2_formulation)

mc_integration = pyblp.Integration('monte_carlo', size=50, specification_options={'seed': 0})

pr_integration = pyblp.Integration('product', size=5)

mc_problem = pyblp.Problem(product_formulations, product_data, integration=mc_integration)
print(mc_problem)
pr_problem = pyblp.Problem(product_formulations, product_data, integration=pr_integration)
print(pr_problem)

bfgs = pyblp.Optimization('bfgs', {'gtol': 1e-10})

results1 = mc_problem.solve(sigma=np.ones((4, 4)), optimization=bfgs)
print(results1)

results2 = pr_problem.solve(sigma=np.ones((4, 4)), optimization=bfgs)
print(results2)

results3 = mc_problem.solve(sigma=np.eye(4), optimization=bfgs)
print(results3)
