import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import sys

def DID1(products, quarterOrMonth):
    panel_data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + "_pre_model_" + quarterOrMonth + "_data.tsv", delimiter = "\t")
    panel_data.set_index(['product-region','time'], inplace=True)
    y = panel_data['log_price']
    exog_vars = ['involvedpostmerger', 'postmerger', quarterOrMonth + '_since_start']
    exog = sm.add_constant(panel_data[exog_vars])
    mod = PanelOLS(y, exog, entity_effects=True)
    fe_res = mod.fit(cov_type = 'clustered', clusters = panel_data['dma_code'])

    beginningtex = """\\documentclass{report}
                      \\usepackage{booktabs}
                      \\begin{document}"""
    endtex = "\end{document}"
    f = open('_'.join([str(elem) for elem in products]) + '_' + quarterOrMonth + '_DID1_A.tex', 'w')
    f.write(beginningtex)
    f.write(fe_res.summary.as_latex())
    f.write(endtex)
    f.close()

product1 = sys.argv[1]
product2 = sys.argv[2]
products = [product1, product2]
quarterOrMonth = sys.argv[3]
DID1(products, quarterOrMonth)
