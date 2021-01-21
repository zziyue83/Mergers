
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
        return (False, c4)

    elif merging_sum == 3:
        return (True, c4)

    elif merging_sum == 2:

        df_merging = overlap_file[overlap_file['merging_party'] == 1]

        if ((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0)):
            return (False, c4)

        else:
            return (True, c4)


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

    aggregated['post_merger'] = []
    aggregated['se_pm'] = []
    aggregated['pv_pm'] = []

    aggregated['post_merger_merging'] = []
    aggregated['se_pmm'] = []
    aggregated['pv_pmm'] = []

    aggregated['post_merger_1y'] = []
    aggregated['se_pm_1y'] = []
    aggregated['pv_pm_1y'] = []

    aggregated['post_merger_merging_1y'] = []
    aggregated['se_pmm_1y'] = []
    aggregated['pv_pmm_1y'] = []


    # loop through folders in "All"
    #folders = [folder for folder in os.listdir(base_folder) if folder not in codes]
    #print(folders)
    for folder in folders:

        merger_folder = base_folder + folder + '/output'

        # go inside folders with step5 finished
        if (os.path.exists(merger_folder + '/did_stata_int_month_2.txt')) and check_overlap(merger_folder)[0]:

            estimate_type = ['0', '1', '2', '3']

            for est_type in estimate_type:

                read_file = pd.read_csv(merger_folder + "/did_stata_int_month_" + est_type + ".txt", sep = "\t")
                read_file = read_file.replace(np.nan, '', regex=True)
                read_file.to_csv(merger_folder + "/did_stata_int_month_" + est_type + ".csv", index=None)

            did_merger = pd.read_csv(merger_folder + '/' + 'did_stata_int_month_2.csv', sep=',')
            did_merger.index = did_merger['Unnamed: 0']

            print(folder)

            # recover only betas for which post_merger_merging exists
            if 'post_merger_merging_1y' in did_merger.index:

                # append the m_folder name and descriptive stats to the dictionary
                aggregated['merger'].append(folder)

                # loop through specs recovering betas
                aggregated['post_merger'].append(did_merger['(1)']['post_merger'])
                aggregated['se_pm'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger')+1)])
                aggregated['pv_pm'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger')+2)])

                aggregated['post_merger_merging'].append(did_merger['(1)']['post_merger_merging'])
                aggregated['se_pmm'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger_merging')+1)])
                aggregated['pv_pmm'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger_merging')+2)])

                aggregated['post_merger_1y'].append(did_merger['(1)']['post_merger_1y'])
                aggregated['se_pm_1y'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger_1y')+1)])
                aggregated['pv_pm_1y'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger_1y')+2)])

                aggregated['post_merger_merging_1y'].append(did_merger['(1)']['post_merger'])
                aggregated['se_pmm_1y'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger_merging_1y')+1)])
                aggregated['pv_pmm_1y'].append(did_merger['(1)'][(did_merger.index.get_loc('post_merger_merging_1y')+2)])


    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df = df.dropna(axis=1, how='all')
    df = aux.clean_betas(df)
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.rstrip('*')
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.replace(',','')
    df[df.columns[1]] = pd.to_numeric(df[df.columns[1]])
    df.to_csv('output/did_int_agg_1y.csv', sep=',')

# level is either "brandlevel_" or ""
level = sys.argv[1] + '_'

base_folder = '../../../All/'

#problematic codes
codes = (['m_1785984020_11', 'm_2664559020_1', 'm_2735179020_1', 'm_2735179020_4',
        'm_2736521020_10', 'm_2033113020_1_OLD', 'm_2033113020_2',
        'm_2675324040_1', 'm_2033113020_3', 'm_2838188020_1',
        'm_2033113020_3_OLD', 'm_2033113020_2_OLD', 'm_m_2203820020_6',
        'm_2813860020_1'])

log_out = open('output/agg_1y.log', 'w')
log_err = open('output/agg_1y.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

folders = [folder for folder in os.listdir(base_folder) if folder not in codes]

get_betas(folders, base_folder, level)
