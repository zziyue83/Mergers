
#import matplotlib
# matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import re
import os
import pandas as pd
import auxiliary as aux
import numpy as np
import sys



def get_betas(folders, base_folder):

    aggregated = {}
    aggregated['merger'] = []

    for i in range(4):

        for month in range(49):

            month = month + 1

            aggregated['Merging_'+str(month) + '.Months_'+str(i)] = []
            aggregated['se_M_'+str(month) + '.Months_'+str(i)] = []
            aggregated['Non_Merging_'+str(month) + '.Months_'+str(i)] = []
            aggregated['se_NM_'+str(month) + '.Months_'+str(i)] = []

        for month in range(25):

            aggregated['Merging_'+str(month) + '.Months_post_'+str(i)] = []
            aggregated['se_M_'+str(month) + '.Months_post_'+str(i)] = []
            aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(i)] = []
            aggregated['se_NM_'+str(month) + '.Months_post_'+str(i)] = []

            aggregated['Merging_'+str(month) + '.Months_post_2_'+str(i)] = []
            aggregated['se_M_'+str(month) + '.Months_post_2_'+str(i)] = []
            aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(i)] = []
            aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(i)] = []



    for folder in folders:

        merger_folder = base_folder + folder + '/output'

        if os.path.exists(merger_folder + '/Months.xlsx'):

            df = pd.read_excel(merger_folder + '/Months.xlsx', header=None)

            aggregated['merger'].append(folder)

            print(folder)

            # Months Pre and Post
            for Month in range(49):
                month = Month + 1

                # Weights==0
                try:
                    if not np.isnan(df[4][Month]):
                        aggregated['Merging_'+str(month) + '.Months_'+str(0)].append(df[4][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[5][Month]):
                        aggregated['se_M_'+str(month) + '.Months_'+str(0)].append(df[5][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[6][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(0)].append(df[6][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[7][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_'+str(0)].append(df[7][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_'+str(0)].append(np.nan)

                # Weights==1
                try:
                    if not np.isnan(df[16][Month]):
                        aggregated['Merging_'+str(month) + '.Months_'+str(1)].append(df[16][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[17][Month]):
                        aggregated['se_M_'+str(month) + '.Months_'+str(1)].append(df[17][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[18][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(1)].append(df[18][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[19][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_'+str(1)].append(df[19][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_'+str(1)].append(np.nan)

                # Weights==2
                try:
                    if not np.isnan(df[28][Month]):
                        aggregated['Merging_'+str(month) + '.Months_'+str(2)].append(df[28][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[29][Month]):
                        aggregated['se_M_'+str(month) + '.Months_'+str(2)].append(df[29][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[30][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(2)].append(df[30][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[31][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_'+str(2)].append(df[31][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_'+str(2)].append(np.nan)

                # Weights==3
                try:
                    if not np.isnan(df[40][Month]):
                        aggregated['Merging_'+str(month) + '.Months_'+str(3)].append(df[40][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[41][Month]):
                        aggregated['se_M_'+str(month) + '.Months_'+str(3)].append(df[41][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[42][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(3)].append(df[42][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[43][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_'+str(3)].append(df[43][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_'+str(3)].append(np.nan)

            # Months Post
            for Month in range(25):
                Month = Month + 24
                month = Month - 24
                # Weights==0
                try:
                    if not np.isnan(df[0][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(0)].append(df[0][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[1][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(0)].append(df[1][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[2][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(0)].append(df[2][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[3][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(0)].append(df[3][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_'+str(0)].append(np.nan)

                # Weights==1
                try:
                    if not np.isnan(df[12][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(1)].append(df[12][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[13][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(1)].append(df[13][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[14][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(1)].append(df[14][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[15][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(1)].append(df[5][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_'+str(1)].append(np.nan)

                # Weights==2
                try:
                    if not np.isnan(df[24][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(2)].append(df[24][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[25][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(2)].append(df[25][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[26][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(2)].append(df[26][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[27][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(2)].append(df[27][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_'+str(2)].append(np.nan)

                # Weights==3
                try:
                    if not np.isnan(df[36][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(3)].append(df[36][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[37][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(3)].append(df[37][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[38][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(3)].append(df[38][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[39][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(3)].append(df[39][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_'+str(3)].append(np.nan)

            # Months Post 2
            for Month in range(25):
                Month = Month + 24
                month = Month - 24
                # Weights==0
                try:
                    if not np.isnan(df[8][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(0)].append(df[8][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[9][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(0)].append(df[9][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[10][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(0)].append(df[10][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)

                try:
                    if not np.isnan(df[11][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(0)].append(df[11][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(0)].append(np.nan)

                # Weights==1
                try:
                    if not np.isnan(df[20][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(1)].append(df[20][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[21][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(1)].append(df[21][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[22][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(1)].append(df[22][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)

                try:
                    if not np.isnan(df[23][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(1)].append(df[23][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(1)].append(np.nan)

                # Weights==2
                try:
                    if not np.isnan(df[32][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(2)].append(df[32][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[33][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(2)].append(df[33][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[34][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(2)].append(df[34][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)

                try:
                    if not np.isnan(df[35][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(2)].append(df[35][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(2)].append(np.nan)

                # Weights==3
                try:
                    if not np.isnan(df[44][Month]):
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(3)].append(df[44][Month])
                    else:
                        aggregated['Merging_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['Merging_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[45][Month]):
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(3)].append(df[45][Month])
                    else:
                        aggregated['se_M_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['se_M_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[46][Month]):
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(3)].append(df[46][Month])
                    else:
                        aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['Non_Merging_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)

                try:
                    if not np.isnan(df[47][Month]):
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(3)].append(df[48][Month])
                    else:
                        aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)
                except KeyError:
                    aggregated['se_NM_'+str(month) + '.Months_post_2_'+str(3)].append(np.nan)



    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df = df.dropna(axis=1, how='all')
    df = aux.clean_betas(df)
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.rstrip('*')
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.replace(',', '')
    df[df.columns[1]] = pd.to_numeric(df[df.columns[1]])
    df.to_csv('output/did_agg_Months.csv', sep=',')


base_folder = '../../../All/'

# problematic codes
codes = (['m_1785984020_11', 'm_2664559020_1', 'm_2735179020_1',
          'm_2735179020_4', 'm_2736521020_10', 'm_2033113020_1_OLD',
          'm_2033113020_2', 'm_2675324040_1', 'm_2033113020_3',
          'm_2838188020_1', 'm_2033113020_3_OLD', 'm_2033113020_2_OLD',
          'm_m_2203820020_6', 'm_2813860020_1'])

log_out = open('output/agg_months.log', 'w')
log_err = open('output/agg_months.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

folders = [folder for folder in os.listdir(base_folder) if folder not in codes]

get_betas(folders, base_folder)
