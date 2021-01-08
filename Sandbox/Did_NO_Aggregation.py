
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

def check_NO_overlap(merger_folder):

    '''
    For a given merger_folder, it opens the overlap.csv file
    checks how many merger parties are there. If there are two,
    the only case where there's doubt left, it checks the structure
    of the pre - post share matrix for the merging parties and
    concludes. It returns True or False, and the C4 measure.
    '''

    overlap_file = pd.read_csv(merger_folder + '/overlap.csv', sep=',')
    merging_sum = overlap_file['merging_party'].sum()
    c4 = overlap_file['pre_share'].nlargest(4).sum()

    if merging_sum < 2:
        return (True, c4, merging_sum)

    elif merging_sum == 3:
        return (False, c4, merging_sum)

    elif merging_sum == 2:

        df_merging = overlap_file[overlap_file['merging_party'] == 1]

        if ((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0)):
            return (True, c4, merging_sum)

        else:
            return (False, c4, merging_sum)

def get_betas(folders, base_folder, level):

    '''
    At the base_folder, it loops through all m_code folders,
    checks whether the brand_level routine is done, and retrieves
    the coefficients, standard erros, and p-values of that routine.
    It generates the "output/aggregated_brand.csv" file.
    '''

    # Auxiliary variable
    level = level.replace('upc_', '')
    print(level)

    if len(level)>0:
        level2 = '_' + level[:-1]
    else:
        level2 = ''
    print(level2)

    # Dictionary with the descriptive variables
    aggregated = {}
    aggregated['merger'] = []
    aggregated['merging_parties'] = []
    aggregated['pre_hhi'] = []
    aggregated['post_hhi'] = []
    aggregated['dhhi'] = []
    aggregated['c4'] = []

    # Adding all the specs-vars to the Dictionary
    for i in range(45):

        j = i+1
        aggregated['post_merger'+'_'+str(j)] = []
        aggregated['se_pm_'+str(j)] = []
        aggregated['pv_pm_'+str(j)] = []

        aggregated['post_merger_merging_'+str(j)] = []
        aggregated['se_pmm_'+str(j)] = []
        aggregated['pv_pmm_'+str(j)] = []

        aggregated['post_merger_major_'+str(j)] = []
        aggregated['se_pmmaj_'+str(j)] = []
        aggregated['pv_pmmaj_'+str(j)] = []

    # loop through folders in "All"
    #folders = [folder for folder in os.listdir(base_folder) if folder not in codes]
    #print(folders)
    for folder in folders:

        merger_folder = base_folder + folder + '/output'
        #print(merger_folder + '/'+level+'did_stata_month_2.csv')
        #print(merger_folder + '/../intermediate/stata_did_month'+level2+'.csv')

        # go inside folders with step5 finished
        if (os.path.exists(merger_folder + '/'+level+'did_stata_month_2.csv')) and check_NO_overlap(merger_folder)[0]:

            did_merger = pd.read_csv(merger_folder + '/'+level+'did_stata_month_2.csv', sep=',')
            did_merger.index = did_merger['Unnamed: 0']

            descr_data = pd.read_csv(
                merger_folder + '/../intermediate/stata_did_month'+level2+'.csv', sep=',')

            print(folder)

            # recover only betas for which post_merger_merging exists
            if 'post_merger_merging' in did_merger.index:

                # append the m_folder name and descriptive stats to the dictionary
                aggregated['merger'].append(folder)
                aggregated['merging_parties'].append(check_NO_overlap(merger_folder)[2])
                aggregated['c4'].append(check_NO_overlap(merger_folder)[1])
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

                    aggregated['post_merger_' + i].append(did_merger[i]['post_merger'])
                    aggregated['se_pm_' + i].append(did_merger[i]
                                                  [(did_merger.index.get_loc('post_merger')+1)])
                    aggregated['pv_pm_' + i].append(did_merger[i]
                                                    [(did_merger.index.get_loc('post_merger')+2)])

                    aggregated['post_merger_merging_' + i].append(did_merger[i]['post_merger_merging'])
                    aggregated['se_pmm_' + i].append(did_merger[i]
                                                  [(did_merger.index.get_loc('post_merger_merging')+1)])
                    aggregated['pv_pmm_' + i].append(did_merger[i]
                                                    [(did_merger.index.get_loc('post_merger_merging')+2)])

                    aggregated['post_merger_major_' + i].append(did_merger[i]['post_merger_major'])
                    aggregated['se_pmmaj_' + i].append(did_merger[i]
                                                  [(did_merger.index.get_loc('post_merger_major')+1)])
                    aggregated['pv_pmmaj_' + i].append(did_merger[i]
                                                    [(did_merger.index.get_loc('post_merger_major')+2)])


    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df = df.dropna(axis=1, how='all')
    df = aux.clean_betas(df)

    df.to_csv('output/aggregated_NO_'+level2+'.csv', sep=',')


# level is either "brandlevel_" or ""
level = sys.argv[1] + '_'

base_folder = '../../../All/'

log_out = open('output/aggregation_NO'+level+'.log', 'w')
log_err = open('output/aggregation_NO'+level+'.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

folders = os.listdir(base_folder)

get_betas(folders, base_folder, level)
