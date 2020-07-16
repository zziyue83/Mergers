import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import sys

def DID1(products, quarterOrMonth):
    panel_data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + "_pre_model_" + quarterOrMonth + "_data.tsv", delimiter = "\t")
    panel_data.set_index(['product-region','time'], inplace=True)
    y = panel_data['log_adjusted_price']
    exog_vars = ['involvedpostmerger', 'postmerger', quarterOrMonth + '_since_start', 'log_employment_rate', 'log_adjusted_hhinc_per_person_mean']
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

<<<<<<< HEAD
products = [sys.argv[1], sys.argv[2]]
quarterOrMonth = sys.argv[3]
#products = [sys.argv[1]]
#quarterOrMonth = sys.argv[2]
=======
#products = [sys.argv[1], sys.argv[2]]
#quarterOrMonth = sys.argv[3]
products = [sys.argv[1]]
quarterOrMonth = sys.argv[2]
>>>>>>> 60263bd182d4190d5acc2accfbd420a51a7136d3
DID1(products, quarterOrMonth)
