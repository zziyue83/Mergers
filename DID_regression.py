import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import sys
import pickle

def MakeTimeDummy(times, mergingt, frequency):
    timeDummyDf = pd.DataFrame(columns = ['t', 'post_merger'])
    if frequency == 'quarter':
        merging_year = int(mergingt[0:4])
        merging_q = int(mergingt[-1])
        for quarter in times:
            year = int(quarter[0:4])
            q = int(quarter[-1])
            if (year>= merging_year and q >= merging_q) or (year > merging_year):
                post_merger = 1
            else:
                post_merger = 0
            timeDummyDf = timeDummyDf.append({'t': quarter, 'post_merger':post_merger}, ignore_index = True)
    elif frequency == 'month':
        merging_year = int(mergingt[0:4])
        merging_m = int(mergingt[4:])
        for month in times:
            year = int(month[0:4])
            m = int(month[4:])
            if (year>= merging_year and m >= merging_m) or (year > merging_year):
                post_merger = 1
            else:
                post_merger = 0
            timeDummyDf = timeDummyDf.append({'t': month, 'post_merger':post_merger}, ignore_index = True)
    else:
        return None
    return timeDummyDf

def AggDMAPrePostSize(product, frequency, mergingt):
    dma_frequency_volume = pd.read_csv("../../GeneratedData/"+product+"_dma_every_"+frequency+"_mkt_volume.tsv", delimiter = '\t')
    dma_frequency_volume[frequency+'_str'] = dma_frequency_volume[frequency].astype(str)
    times = dma_frequency_volume[frequency+'_str'].unique()
    timeDummyDf = MakeTimeDummy(times, mergingt, frequency)
    dma_frequency_volume = dma_frequency_volume.merge(timeDummyDf, how = 'left', left_on = frequency+'_str', right_on = 't')
    dma_prepost_volume = dma_frequency_volume.groupby(['dma_code','post_merger'], as_index = False).agg({'volume':'sum'}).reindex(columns = dma_frequency_volume.columns)
    dma_prepost_volume['dma_postmerger'] = dma_prepost_volume['dma_code'].astype(str)+dma_prepost_volume['post_merger'].astype(str)
    dma_prepost_volume = dma_prepost_volume.set_index('dma_postmerger')
    return dma_frequency_volume[['dma_code', 'post_merger', 'volume']]

def DID_regression(product, frequency, share, mergingt):
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

        beginningtex = """\\documentclass{report}a
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
        prepostDMAsize = AggDMAPrePostSize(product, frequency, mergingt)
        print(prepostDMAsize)
        data['dma_postmerger'] = data['dma_code'].astype(str)+data['post_merger'].astype(str)
        prepostSizeMap = prepostDMAsize.to_dict()

        firmDMAVolume = data[['owner','dma_code','post_merger','volume']]
        firmDMAVolume = firmDMAVolume.groupby(['owner','dma_code','post_merger'], as_index = False).agg({'volume' : 'sum'}).reindex(columns = firmDMAVolume.columns)
        print(firmDMAVolume)

        # dma_month_volume = dma_month_volume.merge(data, how = 'inner', left_on = frequency, right_on = frequency)
        # dma_pre_post_merger_volume = data.groupby(['dma','post_merger'], as_index = False).aggregate({'volume': 'sum'}).reindex(columns = data.columns)
        # dma_pre_post_merger_volume = dma_pre_post_merger_volume[['dma','post_merger','volume']]
        # dma_pre_post_merger_volume.to_csv('trial.csv', sep = '\t')

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
if len(sys.argv) > 4:
    mergingt = sys.argv[4]
else:
    mergingt = '0'
print(product)
DID_regression(product, frequency, mktshare, mergingt)
