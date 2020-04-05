import pandas as pd
import sys
import numpy as np

def preModelData(products, quarterOrMonth, mergingyear, mergingquarterormonth, involvedcompanies):
    panel_data = pd.DataFrame()
    for product in products:
        market_size = pd.read_csv("../../GeneratedData/" + product + "_market_size_" + quarterOrMonth + ".tsv", delimiter = "\t")
        market_size.rename(columns = {'volume':'market_size'}, inplace = True)
        market_size_DMA = market_size.groupby('dma_code').agg({'market_size': 'max'})*1.5
        chunks = pd.read_csv("../../GeneratedData/" + product + "_dma_" + quarterOrMonth + "_upc_top100.tsv", delimiter = "\t", index_col = 0, chunksize = 1000000)
        for data_chunk in chunks:
            data_chunk['log_price'] = np.log(data_chunk['price'])
            data_chunk = data_chunk.join(market_size.set_index(['dma_code', quarterOrMonth]), on=['dma_code', quarterOrMonth])
            data_chunk['market_size_DMA'] = data_chunk['dma_code'].map(market_size_DMA['market_size'])
            data_chunk['market_share'] = data_chunk['volume']/data_chunk['market_size_DMA']
            if quarterOrMonth == 'quarter':
                data_chunk['postmerger'] = np.where((data_chunk['year'] < int(mergingyear)) | ((data_chunk['year']==int(mergingyear)) & (data_chunk['# quarter'] < int(mergingquarterormonth))), 0, 1)
                quarterOrMonth_since_start_dictionary = {'2006Q1': 0, '2006Q2': 1, '2006Q3': 2, '2006Q4': 3, '2007Q1': 4, '2007Q2': 5, '2007Q3': 6, '2007Q4': 7, '2008Q1': 8, '2008Q2': 9, '2008Q3': 10, '2008Q4': 11, '2009Q1': 12, '2009Q2': 13, '2009Q3': 14, '2009Q4': 15}
            if quarterOrMonth == 'month':
                data_chunk['postmerger'] = np.where((data_chunk['year'] < int(mergingyear)) | ((data_chunk['year']==int(mergingyear)) & (data_chunk['# month'] < int(mergingquarterormonth))), 0, 1)
                quarterOrMonth_since_start_dictionary = {200601: 0, 200602: 1, 200603: 2, 200604: 3, 200605: 4, 200606: 5, 200607: 6, 200608: 7, 200609: 8, 200610: 9, 200611: 10, 200612: 11, 200701: 12, 200702: 13, 200703: 14, 200704: 15, 200705: 16, 200706: 17, 200707: 18, 200708: 19, 200709: 20, 200710: 21, 200711: 22, 200712: 23, 200801: 24, 200802: 25, 200803: 26, 200804: 27, 200805: 28, 200806: 29, 200807: 30, 200808: 31, 200809: 32, 200810: 33, 200811: 34, 200812: 35, 200901: 36, 200902: 37, 200903: 38, 200904: 39, 200905: 40, 200906: 41, 200907: 42, 200908: 43, 200909: 44, 200910: 45, 200911: 46, 200912: 47}
            data_chunk[quarterOrMonth + '_since_start'] = data_chunk[quarterOrMonth].map(quarterOrMonth_since_start_dictionary)
            data_chunk['involved'] = np.where((data_chunk['owner company'].isin(involvedcompanies)), 1, 0)
            data_chunk['involvedpostmerger'] = data_chunk['involved']*data_chunk['postmerger']
            data_chunk['product-region'] = data_chunk['upc'].astype(str) + ' ' + data_chunk['dma_code'].astype(str)
            data_chunk['time'] = data_chunk[quarterOrMonth + '_since_start']
            data_chunk = data_chunk.set_index(['product-region','time'])
            if panel_data.empty:
                panel_data = data_chunk
            else:
                panel_data = pd.concat([panel_data,data_chunk])
    panel_data.to_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + "_pre_model_" + quarterOrMonth + "_data.tsv", sep = '\t', encoding = 'utf-8')

quarterOrMonth = sys.argv[1]
mergingyear = sys.argv[2]
mergingquarterormonth = sys.argv[3]
#products = [sys.argv[4], sys.argv[5]]
products = [sys.argv[4]]
involvedcompanies = [sys.argv[5],sys.argv[6]+' '+sys.argv[7],sys.argv[8]]
#involvedcompanies = sys.argv[6]
preModelData(products, quarterOrMonth, mergingyear, mergingquarterormonth, involvedcompanies)
#SABMiller Molson Coors MillerCoors
