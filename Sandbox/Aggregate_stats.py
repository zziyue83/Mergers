import re
import os
import pandas as pd
import sys
import numpy as np

def get_stats(base_folder):

    stats = {}
    stats['merger'] = []

    quantiles = [0, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.98, 0.99, 1]

    for q in quantiles:
        stats['DHHI_'+str(q)] = []
        stats['HHI_'+str(q)] = []
        stats['CTLBR_Share_'+str(q)] = []
        stats['MP_Share_'+str(q)] = []

    folders = [folder for folder in os.listdir(base_folder)]

    for folder in folders:

        data_path = '../../../All/' + folder + '/intermediate/'

        print(data_path)

        if os.path.exists(data_path + 'stata_did_int_month.csv'):

            print(folder)

            df = pd.read_csv(data_path + 'stata_did_int_month.csv', sep=',')

            if 'owner' in df.columns:

                stats['merger'].append(folder)

                c = df.groupby(['dma_code'])[['dhhi', 'post_hhi']].mean()

                df.loc[df['owner']=='Several owners', 'owner'] = 'several owners'
                df.loc[df['owner']=='Several Owners', 'owner'] = 'several owners'

                d = df[(df['owner']=='several owners')]
                d = df.groupby(['dma_code','year','month'])[['shares']].mean()

                for q in quantiles:
                    stats['DHHI_'+str(q)].append(c.dhhi.quantile(q))
                    stats['HHI_'+str(q)].append(c.post_hhi.quantile(q))
                    stats['CTLBR_Share_'+str(q)].append(d.shares.quantile(q))


                #keep only data for merging parties before the merger
                df = df[(df['merging']==True) & (df['post_merger']==0)]

                #generate the sum of volume for each dma_code (mp_volume)
                a = df.groupby('dma_code')['volume'].sum()
                df = pd.merge(df, a, on='dma_code')

                #generate mkt_size for the dma_code
                df['mkt_size'] = df['volume_x']/df['shares']

                #generate the total size for the dma_code before the merger
                b = df.groupby(['dma_code', 'year', 'month'])['mkt_size'].mean()
                b = b.groupby('dma_code').sum()
                df = pd.merge(df, b, on='dma_code')
                df['mp_shares'] = df['volume_y']/df['mkt_size_y']

                for q in quantiles:
                    stats['MP_Share_'+str(q)].append(df.mp_shares.quantile(q))

    df = pd.DataFrame.from_dict(stats)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df.to_csv('output/stats.csv', sep=',')


base_folder = '../../../All/'

log_out = open('output/Sum_Stats.log', 'w')
log_err = open('output/Sum_Stats.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

get_stats(base_folder)
