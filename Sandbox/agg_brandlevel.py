
#import matplotlib
# matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import re
import os
import pandas as pd
import auxiliary as aux
import numpy as np
import sys
import statsmodels.api as sm
from statsmodels.iolib.summary2 import summary_col
import seaborn as sns
import array_to_latex as a2l

sns.set(style='ticks')
colors = ['#838487', '#1b1c1c']
sns.set_palette(sns.color_palette(colors))


def check_overlap(merger_folder):

    overlap_file = pd.read_csv(merger_folder + '/overlap.csv', sep=',')
    merging_sum = overlap_file['merging_party'].sum()
    c4 = overlap_file['pre_share'].nlargest(4).sum()

    if merging_sum < 2:
        return (False, c4)

    elif merging_sum == 3:
        return (True, c4)

    elif merging_sum == 2:

        df_merging = overlap_file[overlap_file['merging_party'] == 1]

        if ((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0)):
            return (False, c4)

        else:
            return (True, c4)


def get_betas(base_folder):

    # basic specs
    base_folder = '../../../All/'
    aggregated = {}
    aggregated['merger'] = []
    aggregated['pre_hhi'] = []
    aggregated['post_hhi'] = []
    aggregated['dhhi'] = []
    aggregated['c4'] = []
    #coefficient = str(coefficient)

    for i in range(45):

        j = i+1
        aggregated['post_merger'+'_'+str(j)] = []
        aggregated['se_pm_'+str(j)] = []
        aggregated['pval_pm_'+str(j)] = []

        aggregated['post_merger_dhhi_'+str(j)] = []
        aggregated['se_pmmd_'+str(j)] = []
        aggregated['pval_pmmd_'+str(j)] = []

    # loop through folders in "All"
    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        # go inside folders with step5 finished
        if (os.path.exists(merger_folder + '/brandlevel_did_stata_month_2.csv')) and check_overlap(merger_folder)[0]:

            did_merger = pd.read_csv(merger_folder + '/brandlevel_did_stata_month_2.csv', sep=',')
            did_merger.index = did_merger['Unnamed: 0']

            descr_data = pd.read_csv(
                merger_folder + '/../intermediate/stata_did_month_brandlevel.csv', sep=',')
            # recover only betas for which post_merger_merging exists
            if 'post_merger_dhhi' in did_merger.index:

                # append the m_folder name and descriptive stats to the dictionary
                aggregated['merger'].append(folder)
                aggregated['c4'].append(check_overlap(merger_folder)[1])
                aggregated['pre_hhi'].append(descr_data.pre_hhi.mean())
                aggregated['post_hhi'].append(descr_data.post_hhi.mean())
                aggregated['dhhi'].append(descr_data.dhhi.mean())

                # rename col names (just in case someone opened and saved in excel).
                if '(1)' in did_merger.columns:

                    for i in did_merger.columns[1:]:

                        did_merger.rename(
                            columns={i: i.lstrip('(').rstrip(')')}, inplace=True)

                else:

                    for i in did_merger.columns[1:]:

                        did_merger.rename(
                            columns={i: i.lstrip('-')}, inplace=True)

                    # loop through specs recovering betas
                for i in did_merger.columns[1:46]:

                    aggregated['post_merger_dhhi'+'_'+i].append(did_merger[i]['post_merger_dhhi'])
                    aggregated['se_pmmd_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger_dhhi')+1)])
                    aggregated['pval_pmmd_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger_dhhi')+2)])

                    aggregated['post_merger'+'_' +
                               i].append(did_merger[i]['post_merger'])
                    aggregated['se_pm_'+i].append(did_merger[i]
                                                  [(did_merger.index.get_loc('post_merger')+1)])
                    aggregated['pval_pm_'+i].append(did_merger[i]
                                                    [(did_merger.index.get_loc('post_merger')+2)])

            # else:
            #	assert coefficient, "Coefficient does not exist: %r" % coefficient

    print(len(aggregated['merger']), len(aggregated['pre_hhi']), len(
        aggregated['post_hhi']), len(aggregated['dhhi']))

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
#    df = aux.clean_betas(df)

    df.to_csv('output/aggregated_brand.csv', sep=',')




# coef = sys.argv[1]
# spec = sys.argv[2]
base_folder = '../../../All/'

log_out = open('output/aggregation_brand.log', 'w')
log_err = open('output/aggregation_brand.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

get_betas(base_folder)


