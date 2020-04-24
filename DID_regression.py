import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import sys
import pickle

def MakeOneYearDummy(times, mergingt, frequency):
    timeDummyDf = pd.DataFrame(columns = ['t', 'include'])
    merging_year = int(mergingt[0:4])
    i = 5 if frequency == 'quarter' else 4
    multiplier = 4 if frequency == 'quarter' else 12
    merging_t = int(mergingt[i:])
    for time in times:
        year = int(time[0:4])
        t = int(time[i:])
        difference = (merging_year - year) + (merging_t - t)/multiplier
        if difference > 0 and difference <= 1:
            timeDummyDf = timeDummyDf.append({'t': time, 'include': 1}, ignore_index = True)
        else:
            timeDummyDf = timeDummyDf.append({'t': time, 'include': 0}, ignore_index = True)
    timeDummyDf = timeDummyDf.set_index('t')
    print(timeDummyDf)
    return timeDummyDf

def AdjustInflation(frequency):
    cpiu = pd.read_excel('cpiu_2000_2020.xlsx', header = 11)
    cpiu = cpiu.set_index('Year')
    month_dictionary = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
    cpiu = cpiu.rename(columns = month_dictionary)
    cpiu = cpiu.drop(['HALF1','HALF2'], axis=1)
    cpiu = cpiu.stack()
    cpiu_202001 = float(cpiu.loc[(2020,1)])
    cpiu = cpiu.reset_index().rename(columns = {'level_1':'month',0:'cpiu'})
    if frequency == 'quarter':
        cpiu['quarter'] = cpiu['month'].apply(lambda x: 1 if x <=3 else 2 if ((x>3) & (x<=6)) else 3 if ((x>6) & (x<=9)) else 4)
        cpiu = cpiu.groupby(['Year', frequency]).agg({'cpiu': 'mean'})
    if frequency == 'month':
        cpiu = cpiu.set_index(['Year', frequency])
    cpiu_202001 = float(cpiu.loc[(2020,1)])
    cpiu['price_index'] = cpiu_202001/cpiu['cpiu']
    cpiu = cpiu.reset_index()
    cpiu['t'] = cpiu['Year'] * 100 + cpiu[frequency]
    return cpiu
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

def CalDMADeltaHHI(oneYearFirmDMA, product, frequency):
    #I am only assuming the fact that the mergers don't divest their brands to outside-merger owner here
    merger = oneYearFirmDMA[oneYearFirmDMA['merging'] == 1]
    print(merger)
    print(merger.owner.unique())
    preMerger = merger.groupby(['dma_code', 'owner'], as_index = False).agg({'volume':'sum', 'dma_size':'first'}, as_index = False).reindex(columns = merger.columns)
    preMerger['share'] = preMerger['volume'] / preMerger['dma_size']
    preMerger['pre_merger_share_square'] =preMerger['share'] * preMerger['share']
    postMerger = preMerger.groupby(['dma_code'], as_index = False).agg({'volume':'sum', 'dma_size':'first','share':'sum','pre_merger_share_square':'sum'}, as_index = False).reindex(columns = preMerger.columns)
    postMerger['post_merger_share_square'] = postMerger['share'] * postMerger['share']
    postMerger['DHHI'] = postMerger['post_merger_share_square'] - postMerger['pre_merger_share_square']
    print(postMerger)
    DMADHHI = postMerger[['dma_code','DHHI']].set_index('dma_code')
    print(DMADHHI)
    DMADHHI.to_csv(product+'_'+frequency+'_DHHI.csv', sep = ',')
    return DMADHHI

def DID_regression(product, frequency, share, mergingt, mergers, inflation = False, demographics = False):
    if share == 'NoMktShare':
        data = pd.read_csv("../../GeneratedData/"+product+"_DID_without_share_"+frequency+".tsv", delimiter = '\t')
        if product == 'CANDY':
            gum = pd.read_csv("../../GeneratedData/"+"GUM"+"_DID_without_share_"+frequency+".tsv", delimiter = '\t')
            data = data.append(gum)
        data['post_merger*merging'] = data['post_merger']*data['merging']
        data['dma_upc'] = data['dma_code'].astype(str) + "_" + data['upc'].astype(str)
        data['lprice_'+product] = np.log(data['price'])
        data['trend'] = data[frequency+'s_since_start']
        data = data.set_index(['dma_upc',frequency+'s_since_start'])
        exog_vars = ['post_merger*merging', 'post_merger', 'trend']
        exog = sm.add_constant(data[exog_vars])
        mod = PanelOLS(data['lprice_' + product], exog, entity_effects = True)
        fe_res = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
        print(fe_res)

        beginningtex = """\\documentclass{report}
                          \\usepackage{booktabs}
                          \\begin{document}"""
        endtex = "\end{document}"
        addon = '_GUM' if product == 'CANDY' else ''
        f = open(product + addon + '_DID_NoMktShare_'+frequency+'.tex', 'w')
        f.write(beginningtex)
        f.write(fe_res.summary.as_latex())
        f.write(endtex)
        f.close()

    elif share == 'MktShare':
        data = pd.read_csv("../../GeneratedData/"+product+"_DID_without_share_"+frequency+".tsv", delimiter = '\t')
        if product == 'CANDY':
            gum = pd.read_csv("../../GeneratedData/"+"GUM"+"_DID_without_share_"+frequency+".tsv", delimiter = '\t')
            data = data.append(gum)
#calculate Herfindahl index
        firmDMA = data[['owner','dma_code',frequency,'volume','merging']]
        firmDMA = firmDMA[firmDMA['owner'] != 'unknown']
        firmDMA['time_str'] = firmDMA[frequency].astype(str)
        times = firmDMA['time_str'].unique()
        oneYearDummy = MakeOneYearDummy(times, mergingt, frequency)
        firmDMA = firmDMA.merge(oneYearDummy, how = 'inner', left_on = 'time_str', right_on = 't')
        oneYearFirmDMA = firmDMA[firmDMA['include'] == 1]
        DMAVolume = oneYearFirmDMA.groupby(['dma_code'], as_index = False).agg({'volume':'sum'}, as_index = False).reindex(columns = oneYearFirmDMA.columns)
        DMAVolume = DMAVolume[['dma_code','volume']].set_index('dma_code')
        DMAVolumeMap =DMAVolume.to_dict()
        print(DMAVolume)
        oneYearFirmDMA['dma_size'] = oneYearFirmDMA['dma_code'].map(DMAVolumeMap['volume'])
        DMADHHI = CalDMADeltaHHI(oneYearFirmDMA, product, frequency)
        DMAConcentrationMap = DMADHHI.to_dict()

        data['DHHI'] = data['dma_code'].map(DMAConcentrationMap['DHHI'])
        data['DHHI*post_merger'] = data['DHHI']*data['post_merger']
        data['dma_upc'] = data['dma_code'].astype(str) + "_" + data['upc'].astype(str)
        data['lprice_'+product] = np.log(data['price'])
        data['trend'] = data[frequency+'s_since_start']
        data = data.set_index(['dma_upc',frequency+'s_since_start'])
        exog_vars = ['DHHI*post_merger', 'post_merger', 'trend']
        exog = sm.add_constant(data[exog_vars])
        print(data[exog_vars])
        mod = PanelOLS(data['lprice_' + product], exog, entity_effects = True)
        fe_res = mod.fit(cov_type = 'clustered', clusters = data['dma_code'])
        print(fe_res)

        beginningtex = """\\documentclass{report}
                          \\usepackage{booktabs}
                          \\begin{document}"""
        endtex = "\end{document}"
        addon = '_GUM' if product == 'CANDY' else ''
        f = open(product + addon + '_DID_MktShare_'+frequency+'.tex', 'w')
        f.write(beginningtex)
        f.write(fe_res.summary.as_latex())
        f.write(endtex)
        f.close()

        cpiu = AdjustInflation(frequency)
        cpiu.set_index('t')
        cpiu
        data['cpiu'] = data

if __name__ == "__main__":

    cpi = AdjustInflation('month')
    print(cpi)
    cpi = AdjustInflation('quarter')
    print(cpi)
    # if len(sys.argv) < 3:
    #     print("Not enough arguments")
    #     sys.exit()
    #
    # product = sys.argv[1]
    # frequency = sys.argv[2]
    # mktshare = sys.argv[3]
    # if len(sys.argv) > 4:
    #     mergingt = sys.argv[4]
    # else:
    #     mergingt = '0'
    # print(product)
    # mergersMap = {'CANDY':['Mars', 'Wrigley'],'GUM':['Mars', 'Wrigley'], 'BEER': ['SABMiller', 'Molson Coors']}
    # DID_regression(product, frequency, mktshare, mergingt,mergersMap[product])
    # # DID_regression(product, frequency, mktshare, mergingt,['SABMiller', 'Molson Coors'])
