import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import sys
import pickle

def MakeOwnerDummy(mergers, all_owners):
    ownerDummyDf = pd.DataFrame(columns = ['owner', 'merging'])
    for merger in mergers:
        ownerDummyDf = ownerDummyDf.append({'owner': merger, 'merging':1}, ignore_index = True)
    for owner in all_owners:
        if owner not in mergers:
            ownerDummyDf = ownerDummyDf.append({'owner': owner, 'merging':0}, ignore_index = True)
    print(ownerDummyDf)
    return ownerDummyDf

# def MakeTimeDummy(times, mergingt, frequency):
#     timeDummyDf = pd.DataFrame(columns = ['t', 'post_merger'])
#     if frequency == 'quarter':
#         merging_year = int(mergingt[0:4])
#         merging_q = int(mergingt[-1])
#         for quarter in times:
#             year = int(quarter[0:4])
#             q = int(quarter[-1])
#             if (year>= merging_year and q >= merging_q) or (year > merging_year):
#                 post_merger = 1
#             else:
#                 post_merger = 0
#             timeDummyDf = timeDummyDf.append({'t': quarter, 'post_merger':post_merger}, ignore_index = True)
#     elif frequency == 'month':
#         merging_year = int(mergingt[0:4])
#         merging_m = int(mergingt[4:])
#         for month in times:
#             year = int(month[0:4])
#             m = int(month[4:])
#             if (year>= merging_year and m >= merging_m) or (year > merging_year):
#                 post_merger = 1
#             else:
#                 post_merger = 0
#             timeDummyDf = timeDummyDf.append({'t': month, 'post_merger':post_merger}, ignore_index = True)
#     else:
#         return None
#     return timeDummyDf

def MakeOneYearDummy(times, mergingt, frequency):
    timeDummyDf = pd.DataFrame(columns = ['t', 'include'])
    merging_year = int(mergingt[0:4])
    i = 5 if frequency == 'quarter' else 5
    multiplier = 4 if frequency == 'quarter' else 12
    merging_t = int(merging[i:])
    for time in times:
        year = int(time[0:4])
        t = int(time[i:])
        difference = (merging_year - year) + (mergingt - t)/multiplier
        if difference > 0 and difference <= 1:
            timeDummyDf = timeDummyDf.append({'t': time, 'include': 1}, ignore_index = True)
        else:
            timeDummyDf = timeDummyDf.append({'t': time, 'include': 0}, ignore_index = True)
    timeDummyDf = timeDummyDf.set_index('t')
    print(timeDummyDf)
    return timeDummyDf

# def AggDMAPrePostSize(product, frequency, mergingt):
#     dma_frequency_volume = pd.read_csv("../../GeneratedData/"+product+"_dma_every_"+frequency+"_mkt_volume.tsv", delimiter = '\t')
#     dma_frequency_volume['time_str'] = dma_frequency_volume[frequency].astype(str)
#     times = dma_frequency_volume['time_str'].unique()
#     timeDummyDf = MakeTimeDummy(times, mergingt, frequency)
#     dma_frequency_volume = dma_frequency_volume.merge(timeDummyDf, how = 'left', left_on = 'time_str', right_on = 't')
#     dma_prepost_volume = dma_frequency_volume.groupby(['dma_code','post_merger'], as_index = False).agg({'volume':'sum'}).reindex(columns = dma_frequency_volume.columns)
#     dma_prepost_volume['dma_postmerger'] = dma_prepost_volume['dma_code'].astype(str)+dma_prepost_volume['post_merger'].astype(str)
#     dma_prepost_volume = dma_prepost_volume.set_index('dma_postmerger')
#     return dma_prepost_volume[['dma_code', 'post_merger', 'volume']]

# def CalDMAMktSize(topBrandsDMAVolume, includeTimeDf, frequency):
#     topBrandsDMAVolume['time_str'] = topBrandsDMAVolume[frequency].astype(str)
#     topBrandsDMAVolume = topBrandsDMAVolume.merger(includeTimeDf, how = 'inner', left_on = 'time_str', right_on = 't')
#     topBrandsDMAVolume = topBrandsDMAVolume[topBrandsDMAVolume['include'] == 1]
#     DMAVolume = topBrandsDMAVolume.groupby(['dma_code']).agg({'volume':'sum'}, as_index = False).reindex(columns = topBrandsDMAVolume)
#     DMAVolume = DMAVolume['dma_code','volume'].set_index('dma_code')
#     return DMAVolume

def CalDMADeltaHHI(oneYearFirmDMA):
    #I am only assuming the fact that the mergers don't divest their brands to outside-merger owner here
    merger = oneYearFirmDMA[oneYearFirmDMA['merging'] == 1]
    preMerger = merger.groupby(['dma_code', 'owner']).agg({'volume':'sum', 'dma_size':'first'}, as_index = False).reindex(columns = merger.columns)
    preMerger['share'] = preMerger['volume'] / preMerger['dma_size']
    preMerger['pre_merger_share_square'] =preMerger['share'] * preMerger['share']
    postMerger = preMerger.groupby(['dma_code']).agg({'volume':'sum', 'dma_size':'first','share':'sum','pre_merger_share_square':'sum'}, as_index = False).reindex(columns = preMerger.columns)
    postMerger['post_merger_share_square'] = postMerger['share'] * postMerger['share']
    postMerger['DHHI'] = postMerger['post_merger_share_square'] - postMerger['pre_merger_share_square']
    DMADHHI = postMerger['dma_code','DHHI'].set_index('dma_code')
    print(DMADHHI)
    return postMerger

def DID_regression(product, frequency, share, mergingt, mergers):
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

#calculate Herfindahl index
        owners = pd.read_csv("Top 100 "+product+".csv", delimiter = ',')
        all_owners = owners['owner initial'].unique()
        ownerDummyDf = MakeOwnerDummy(mergers, all_owners)
        # prepostDMASize = AggDMAPrePostSize(product, frequency, mergingt)
        # print(prepostDMASize)
        # data['dma_postmerger'] = data['dma_code'].astype(str)+data['post_merger'].astype(str)
        # prepostSizeMap = prepostDMASize.to_dict()
        firmDMA = data[['owner','dma_code',frequency,'volume']]
        firmDMA = firmDMA.merge(ownerDummyDf, how = 'inner', left_on='owner', right_on = 'owner')
        firmDMA['time_str'] = firmDMA[frequency].astype(str)
        times = firm['time_str'].unique()
        oneYearDummy = MakeOneYearDummy(times, mergingt, frequency)
        firmDMA = firmDMA.merge(oneYearDummy, how = 'inner', left_on = 'time_str', right_on = 't')
        oneYearFirmDMA = firmDMA[firmDMA['include'] == 1]
        DMAVolume = oneYearFirmDMA.groupby(['dma_code']).agg({'volume':'sum'}, as_index = False).reindex(columns = oneYearFirmDMA)
        DMAVolume = DMAVolume['dma_code','volume'].set_index('dma_code')
        DMAVolumeMap =DMAVolume.to_dict()
        print(DMAVolume)
        oneYearFirmDMA['dma_size'] = oneYearFirmDMA['dma_code'].map(DMAVolumeMap)
        DMADHHI = CalDMADeltaHHI(oneYearFirmDMAfirmDMA)
        print(DMADHHI)
        DMAConcentrationMap = DMADHHI.to_dict()


        # firmDMA = firmDMA.groupby(['owner','dma_code','post_merger'], as_index = False).agg({'volume' : 'sum', 'merging':'first'}).reindex(columns = firmDMA.columns)
        # print(firmDMA)
        # firmDMA['dma_postmerger'] = firmDMA['dma_code'].astype(str)+firmDMA['post_merger'].astype(str)
        # firmDMA['dma_size'] = firmDMA['dma_postmerger'].map(prepostDMASize['volume'])
        # firmDMA['share'] = firmDMA['volume'] / firmDMA['dma_size']
        # firmDMA['share_square'] = firmDMA['share'] * firmDMA['share']
        # firmDMA['share_square_post_merger'] = firmDMA['share_square'] * firmDMA['post_merger'] * (1 - firmDMA['merging'])
        # firmDMA['share_square_pre_merger'] = firmDMA['share_square'] * (1 - firmDMA['post_merger'])
        # merger = firmDMA[(firmDMA['post_merger'] == 1) & (firmDMA['merging'] == 1)]
        # print(merger)
        # merger = merger.groupby(['dma_code']).agg({'share':'sum','dma_size':'first','volume':'sum','owner':'first','merging':'first','post_merger': 'first'}, as_index = False).reindex(columns = firmDMA.columns)
        # merger['share_square'] = merger['share'] * merger['share']
        # merger['share_square_post_merger'] = merger['share_square'] * merger['post_merger']
        # merger['share_square_pre_merger'] = 0
        # merger['owner'] = 'merger'
        # print(merger)
        # firmDMA.append(merger)
        # print(firmDMA)
        # DMAConcentration = firmDMA.groupby('dma_code', as_index = False).agg({'volume':'sum','share_square':'sum','share_square_post_merger':'sum','share_square_pre_merger':'sum'}).reindex(columns = firmDMA.columns)
        # DMAConcentration['DHHI'] = DMAConcentration['share_square_post_merger'] - DMAConcentration['share_square_pre_merger']
        # DMAConcentration = DMAConcentration.set_index('dma_code')
        # print(DMAConcentration)
        # DMAConcentrationMap = DMAConcentration.to_dict()
#end of calculating DHHI

        # data['DHHI'] = data['dma_code'].map(DMAConcentrationMap['DHHI'])
        # data['DHHI*post_merger'] = data['DHHI']*data['post_merger']
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
DID_regression(product, frequency, mktshare, mergingt,['SABMiller', 'Molson Coors'])
