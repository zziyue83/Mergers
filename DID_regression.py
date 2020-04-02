import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import sys
import pickle

def DID_regression(product, frequency, share):
    if share == 'NoMktShare':
        data = pd.read_csv("../../GeneratedData/"+product+"_DID_without_share_"+frequency+".tsv", delimiter = '\t')
        data['post_merger*merging'] = data['post_merger']*data['merging']
        data['dma_upc'] = data['dma_code'].astype(str) + "_" + data['upc'].astype(str)
        data['lprice_'+product] = np.log(data['price'])
        data['trend'] = data[frequency+'s_since_start']
        data = data.set_index(['dma_upc',frequency+'s_since_start'])
        exog_vars = ['post_merger*merging', 'post_merger', 'trend']
        exog = sm.add_constant(data[exog_vars])
        mod = PanelOLS(data['lprice_' + product], exog, entity_effects = True)
        fe_res = mod.fit()
        print(fe_res)

        beginningtex = """\\documentclass{report}
                          \\usepackage{booktabs}
                          \\begin{document}"""
        endtex = "\end{document}"
        f = open(product + '_DID_NoMktShare.tex', 'w')
        f.write(beginningtex)
        f.write(fe_res.summary.as_latex())
        f.write(endtex)
        f.close()
    elif share == 'MktShare':
        data = pd.read_csv("../../GeneratedData/"+product+"_DID_without_share_"+frequency+".tsv", delimiter = '\t')
        print('hahahaha')
        dma_month_volume = pd.read_csv("../../GeneratedData/"+product+"_dma_every_"+frequency+"_mkt_volume.tsv", delimiter = '\t')
        print('abababab')
        dma_month_volume = dma_month_volume.merge(data[[frequency,'post_merger']], how = 'inner', left_on = frequency, right_on = frequency)
        print('huhuhuhuhhu')
        dma_pre_post_merger_volume = dma_monthvolume.groupby(['dma','post_merger'], as_index = False).aggregate({'volume': 'sum'}).reindex(columns = dma_month_volume.columns)
        print(dma_pre_post_merger_volume)
        # volumes = data.groupby(['dma','post_merger','owner'])
        # data['DHHI'] = data['HHIAfter'] - data['HHIBefore']
        # data['DHHI*post_merger'] = data['DHHI']*data['merging']
        # data['dma_upc'] = data['dma_code'].astype(str) + "_" + data['upc'].astype(str)
        # data['lprice_'+product] = np.log(data['price'])
        # data['trend'] = data[frequency+'s_since_start']
        # data = data.set_index(['dma_upc',frequency+'s_since_start'])
        # exog_vars = ['DHHI*post_merger', 'post_merger', 'trend']
        # exog = sm.add_constant(data[exog_vars])
        # mod = PanelOLS(data['lprice_' + product], exog, entity_effects = True)
        # fe_res = mod.fit()
        # print(fe_res)
        #
        # beginningtex = """\\documentclass{report}
        #                   \\usepackage{booktabs}
        #                   \\begin{document}"""
        # endtex = "\end{document}"
        # f = open(product + '_DID_MktShare.tex', 'w')
        # f.write(beginningtex)
        # f.write(fe_res.summary.as_latex())
        # f.write(endtex)
        # f.close()

if len(sys.argv) < 3:
    print("Not enough arguments")
    sys.exit()

product = sys.argv[1]
frequency = sys.argv[2]
mktshare = sys.argv[3]
print(product)
DID_regression(product, frequency, mktshare)
