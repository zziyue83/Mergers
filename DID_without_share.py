import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import sys

def DID_regression(product, frequency, share):
    if share == 'NoMktShare':
        data = pd.read_csv("../../GeneratedData/"+product+"_DID_without_share_"+frequency+".tsv", delimiter = '\t')
        data['post_merger*merging'] = data['post_merger']*data['merging']
        data['lprice'] = np.log(data['price'])
        data.set_index(['dma_code','upc'])
        exog_vars = ['post_merger*merging', 'post_merger', frequency+'s_since_start']
        exog = sm.add_constant(data[exog_vars])
        mod = PanelOLS(data['lprice'], exog, entity_effects = True)
        fe_res = mod.fit()
        print(fe_res)

if len(sys.argv) < 3:
    print("Not enough arguments")
    sys.exit()

product = sys.argv[1]
frequency = sys.argv[2]
mktshare = sys.argv[3]
print(product)
DID_regression(product, frequency, mktshare)
