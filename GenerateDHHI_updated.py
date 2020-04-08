import pandas as pd
import sys
import numpy as np

def GenerateDHHI(products, quarterOrMonth, mergingyear, mergingquarterormonth):
    panel_data = pd.read_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + "_pre_model_" + quarterOrMonth + "_data.tsv", delimiter = "\t")
    if quarterOrMonth == 'quarter':
        panel_data['postmerger_a_year_before'] = np.where(((panel_data['year'] == (int(mergingyear)-1)) & (panel_data['# quarter'] >= int(mergingquarterormonth))) | ((panel_data['year'] == int(mergingyear)) & (panel_data['# quarter'] <= (int(mergingquarterormonth)-1))), 0, 1)
    if quarterOrMonth == 'month':
        panel_data['postmerger_a_year_before'] = np.where(((panel_data['year'] == (int(mergingyear)-1)) & (panel_data['# month'] >= int(mergingquarterormonth))) | ((panel_data['year'] == int(mergingyear)) & (panel_data['# month'] <= (int(mergingquarterormonth)-1))), 0, 1)
    pre_merger_data = panel_data[panel_data['postmerger_a_year_before']==0]
    pre_merger_data = pre_merger_data[pre_merger_data['owner initial'] != 'unknown']
    pre_merger_data = pre_merger_data[pre_merger_data['owner last'] != 'unknown']
        
    HHI_before = pre_merger_data.groupby(['owner initial','dma_code',quarterOrMonth]).agg({'volume': 'sum', 'market_size': 'first'})
    HHI_before = HHI_before.groupby(level=[0,1]).agg({'volume': 'sum', 'market_size': 'sum'})
    HHI_before['market_share'] = HHI_before['volume']/HHI_before['market_size']
    HHI_before['HHI_before'] = HHI_before['market_share']**2
    HHI_before = HHI_before.groupby('dma_code').agg({'HHI_before': 'sum'})
    
    HHI_after = pre_merger_data.groupby(['owner last','dma_code',quarterOrMonth]).agg({'volume': 'sum', 'market_size': 'first'})
    HHI_after = HHI_after.groupby(level=[0,1]).agg({'volume': 'sum', 'market_size': 'sum'})
    HHI_after['market_share'] = HHI_after['volume']/HHI_after['market_size']
    HHI_after['HHI_after'] = HHI_after['market_share']**2
    HHI_after = HHI_after.groupby('dma_code').agg({'HHI_after': 'sum'})
    DHHI = HHI_before.merge(HHI_after, left_index = True, right_index = True)
    DHHI['DHHI'] = DHHI['HHI_after'] - DHHI['HHI_before']
    panel_data['DHHI'] = panel_data['dma_code'].map(DHHI['DHHI'])
    panel_data.to_csv("../../GeneratedData/" + '_'.join([str(elem) for elem in products]) + "_DHHI_" + quarterOrMonth + ".tsv", sep = '\t', encoding = 'utf-8')
    
quarterOrMonth = sys.argv[1]
mergingyear = sys.argv[2]
mergingquarterormonth = sys.argv[3]
#products = [sys.argv[4], sys.argv[5]]
products = [sys.argv[4]]
GenerateDHHI(products, quarterOrMonth, mergingyear, mergingquarterormonth)
# quarter 2008 2 CANDY GUM
# month 2008 5 CANDY GUM
