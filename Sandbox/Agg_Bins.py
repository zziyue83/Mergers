
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

    Coarse_Bins = ['0', '1', '2']
    for binc in Coarse_Bins:
        aggregated['post_merger_'+binc+'.HHI'] = []
        aggregated['se_pm'+binc+'.HHI'] = []
        aggregated['pv_pm'+binc+'.HHI'] = []
        aggregated['post_merger_merging_'+binc+'.HHI'] = []
        aggregated['se_pmm'+binc+'.HHI'] = []
        aggregated['pv_pmm'+binc+'.HHI'] = []

        aggregated['post_merger_'+binc+'.DHHI'] = []
        aggregated['se_pm'+binc+'.DHHI'] = []
        aggregated['pv_pm'+binc+'.DHHI'] = []
        aggregated['post_merger_merging_'+binc+'.DHHI'] = []
        aggregated['se_pmm'+binc+'.DHHI'] = []
        aggregated['pv_pmm'+binc+'.DHHI'] = []

        aggregated['post_merger_'+binc+'.DHHI_HHI_NW'] = []
        aggregated['se_pm'+binc+'.DHHI_HHI_NW'] = []
        aggregated['pv_pm'+binc+'.DHHI_HHI_NW'] = []
        aggregated['post_merger_merging_'+binc+'.DHHI_HHI_NW'] = []
        aggregated['se_pmm'+binc+'.DHHI_HHI_NW'] = []
        aggregated['pv_pmm'+binc+'.DHHI_HHI_NW'] = []

    Finer_Bins = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
    for binc in Finer_Bins:
        aggregated['post_merger_'+binc+'.HHIf'] = []
        aggregated['se_pm'+binc+'.HHIf'] = []
        aggregated['pv_pm'+binc+'.HHIf'] = []
        aggregated['post_merger_merging_'+binc+'.HHIf'] = []
        aggregated['se_pmm'+binc+'.HHIf'] = []
        aggregated['pv_pmm'+binc+'.HHIf'] = []

        aggregated['post_merger_'+binc+'.DHHIf'] = []
        aggregated['se_pm'+binc+'.DHHIf'] = []
        aggregated['pv_pm'+binc+'.DHHIf'] = []
        aggregated['post_merger_merging_'+binc+'.DHHIf'] = []
        aggregated['se_pmm'+binc+'.DHHIf'] = []
        aggregated['pv_pmm'+binc+'.DHHIf'] = []

        aggregated['post_merger_'+binc+'.DHHI_HHI'] = []
        aggregated['se_pm'+binc+'.DHHI_HHI'] = []
        aggregated['pv_pm'+binc+'.DHHI_HHI'] = []
        aggregated['post_merger_merging_'+binc+'.DHHI_HHI'] = []
        aggregated['se_pmm'+binc+'.DHHI_HHI'] = []
        aggregated['pv_pmm'+binc+'.DHHI_HHI'] = []

    print(aggregated)

    # loop through folders in "All"
    #folders = [folder for folder in os.listdir(base_folder) if folder not in codes]
    #print(folders)
    for folder in folders:

        merger_folder = base_folder + folder + '/output'

        # go inside folders with step5 finished
        if (os.path.exists(merger_folder + '/did_stata_int_month_2.txt')) and check_overlap(merger_folder)[0]:

            did_merger = pd.read_csv(merger_folder + '/' + 'did_stata_int_month_2.csv', sep=',')
            did_merger.index = did_merger['Unnamed: 0']

            print(folder)

            # append the m_folder name and descriptive stats to the dictionary
            aggregated['merger'].append(folder)

            #Coefficients for HHI Coarse Bins
            for binc in Coarse_Bins:

                #Coefficients for post_merger # i.HHI Coarse Bins
                if ('1.post_merger#'+binc+'b.HHI_bins' in did_merger.index) or ('1.post_merger#'+binc+'.HHI_bins' in did_merger.index):

                    if ('1.post_merger#'+binc+'b.HHI_bins' in did_merger.index):

                        # loop through specs recovering betas
                        aggregated['post_merger_'+binc+'.HHI'].append(did_merger['(2)']['1.post_merger#'+binc+'b.HHI_bins'])
                        aggregated['se_pm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger#'+binc+'b.HHI_bins')+1)])
                        aggregated['pv_pm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger#'+binc+'b.HHI_bins')+2)])

                    elif ('1.post_merger#'+binc+'.HHI_bins' in did_merger.index):

                       # loop through specs recovering betas
                        aggregated['post_merger_'+binc+'.HHI'].append(did_merger['(2)']['1.post_merger#'+binc+'.HHI_bins'])
                        aggregated['se_pm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger#'+binc+'.HHI_bins')+1)])
                        aggregated['pv_pm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger#'+binc+'.HHI_bins')+2)])

                else:

                    aggregated['post_merger_'+binc+'.HHI'].append(np.nan)
                    aggregated['se_pm'+binc+'.HHI'].append(np.nan)
                    aggregated['pv_pm'+binc+'.HHI'].append(np.nan)

            for binc in Coarse_Bins:

                #Coefficients for post_merger_merging # i.HHI coarse bins
                if ('1.post_merger_merging#'+binc+'b.HHI_bins' in did_merger.index) or ('1.post_merger_merging#'+binc+'.HHI_bins' in did_merger.index):

                    if ('1.post_merger_merging#'+binc+'b.HHI_bins' in did_merger.index):

                        # loop through specs recovering betas
                        aggregated['post_merger_merging_'+binc+'.HHI'].append(did_merger['(2)']['1.post_merger_merging#'+binc+'b.HHI_bins'])
                        aggregated['se_pmm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'b.HHI_bins')+1)])
                        aggregated['pv_pmm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'b.HHI_bins')+2)])

                    elif ('1.post_merger_merging#'+binc+'.HHI_bins' in did_merger.index):

                       # loop through specs recovering betas
                        aggregated['post_merger_merging_'+binc+'.HHI'].append(did_merger['(2)']['1.post_merger_merging#'+binc+'.HHI_bins'])
                        aggregated['se_pmm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'.HHI_bins')+1)])
                        aggregated['pv_pmm'+binc+'.HHI'].append(did_merger['(2)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'.HHI_bins')+2)])

                else:

                    aggregated['post_merger_merging_'+binc+'.HHI'].append(np.nan)
                    aggregated['se_pmm'+binc+'.HHI'].append(np.nan)
                    aggregated['pv_pmm'+binc+'.HHI'].append(np.nan)

            #Coefficients for DHHI Coarse Bins
            for binc in Coarse_Bins:

                #post_merger # i.DHHI coarse bins
                if ('1.post_merger#'+binc+'b.DHHI_bins' in did_merger.index) or ('1.post_merger#'+binc+'.DHHI_bins' in did_merger.index):

                    if ('1.post_merger#'+binc+'b.DHHI_bins' in did_merger.index):

                        # loop through specs recovering betas
                        aggregated['post_merger_'+binc+'.DHHI'].append(did_merger['(3)']['1.post_merger#'+binc+'b.DHHI_bins'])
                        aggregated['se_pm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger#'+binc+'b.DHHI_bins')+1)])
                        aggregated['pv_pm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger#'+binc+'b.DHHI_bins')+2)])

                    elif ('1.post_merger#'+binc+'.DHHI_bins' in did_merger.index):

                       # loop through specs recovering betas
                        aggregated['post_merger_'+binc+'.DHHI'].append(did_merger['(3)']['1.post_merger#'+binc+'.DHHI_bins'])
                        aggregated['se_pm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger#'+binc+'.DHHI_bins')+1)])
                        aggregated['pv_pm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger#'+binc+'.DHHI_bins')+2)])

                else:

                    aggregated['post_merger_'+binc+'.DHHI'].append(np.nan)
                    aggregated['se_pm'+binc+'.DHHI'].append(np.nan)
                    aggregated['pv_pm'+binc+'.DHHI'].append(np.nan)


            for binc in Coarse_Bins:

                #post_merger_merging # i.DHHI coarse bins
                if ('1.post_merger_merging#'+binc+'b.DHHI_bins' in did_merger.index) or ('1.post_merger_merging#'+binc+'.DHHI_bins' in did_merger.index):

                    if ('1.post_merger#'+binc+'b.DHHI_bins' in did_merger.index):

                        # loop through specs recovering betas
                        aggregated['post_merger_merging_'+binc+'.DHHI'].append(did_merger['(3)']['1.post_merger_merging#'+binc+'b.DHHI_bins'])
                        aggregated['se_pmm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'b.DHHI_bins')+1)])
                        aggregated['pv_pmm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'b.DHHI_bins')+2)])

                    elif ('1.post_merger_merging#'+binc+'.DHHI_bins' in did_merger.index):

                       # loop through specs recovering betas
                        aggregated['post_merger_merging_'+binc+'.DHHI'].append(did_merger['(3)']['1.post_merger_merging#'+binc+'.DHHI_bins'])
                        aggregated['se_pmm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'.DHHI_bins')+1)])
                        aggregated['pv_pmm'+binc+'.DHHI'].append(did_merger['(3)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'.DHHI_bins')+2)])

                else:

                    aggregated['post_merger_merging_'+binc+'.DHHI'].append(np.nan)
                    aggregated['se_pmm'+binc+'.DHHI'].append(np.nan)
                    aggregated['pv_pmm'+binc+'.DHHI'].append(np.nan)

            # Coefficients for HHI Finer Bins
            for binf in Finer_Bins:

                # post_merger # i.HHI fine bins
                if ('1.post_merger#'+binf+'b.HHI_binsf' in did_merger.index) or ('1.post_merger#'+binf+'.HHI_binsf' in did_merger.index):

                    if ('1.post_merger#'+binf+'b.HHI_binsf' in did_merger.index):

                        aggregated['post_merger_'+binf+'.HHIf'].append(did_merger['(4)']['1.post_merger#'+binf+'b.HHI_binsf'])
                        aggregated['se_pm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger#'+binf+'b.HHI_binsf')+1)])
                        aggregated['pv_pm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger#'+binf+'b.HHI_binsf')+2)])

                    elif ('1.post_merger#'+binf+'.HHI_binsf' in did_merger.index):

                        aggregated['post_merger_'+binf+'.HHIf'].append(did_merger['(4)']['1.post_merger#'+binf+'.HHI_binsf'])
                        aggregated['se_pm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger#'+binf+'.HHI_binsf')+1)])
                        aggregated['pv_pm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger#'+binf+'.HHI_binsf')+2)])

                else:

                    aggregated['post_merger_'+binf+'.HHIf'].append(np.nan)
                    aggregated['se_pm'+binf+'.HHIf'].append(np.nan)
                    aggregated['pv_pm'+binf+'.HHIf'].append(np.nan)


            for binf in Finer_Bins:

                # post_merger_merging # i.HHI fine bins
                if ('1.post_merger_merging#'+binf+'b.HHI_binsf' in did_merger.index) or ('1.post_merger_merging#'+binf+'.HHI_binsf' in did_merger.index):

                    if ('1.post_merger_merging#'+binf+'b.HHI_binsf' in did_merger.index):

                        aggregated['post_merger_merging_'+binf+'.HHIf'].append(did_merger['(4)']['1.post_merger_merging#'+binf+'b.HHI_binsf'])
                        aggregated['se_pmm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'b.HHI_binsf')+1)])
                        aggregated['pv_pmm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'b.HHI_binsf')+2)])

                    elif ('1.post_merger_merging#'+binf+'.HHI_binsf' in did_merger.index):

                        aggregated['post_merger_merging_'+binf+'.HHIf'].append(did_merger['(4)']['1.post_merger_merging#'+binf+'.HHI_binsf'])
                        aggregated['se_pmm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'.HHI_binsf')+1)])
                        aggregated['pv_pmm'+binf+'.HHIf'].append(did_merger['(4)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'.HHI_binsf')+2)])

                else:

                    aggregated['post_merger_merging_'+binf+'.HHIf'].append(np.nan)
                    aggregated['se_pmm'+binf+'.HHIf'].append(np.nan)
                    aggregated['pv_pmm'+binf+'.HHIf'].append(np.nan)


            #Coefficients for DHHI Finer Bins
            for binf in Finer_Bins:

                # post_merger # i.DHHI fine bins
                if ('1.post_merger#'+binf+'b.DHHI_binsf' in did_merger.index) or ('1.post_merger#'+binf+'.DHHI_binsf' in did_merger.index):

                    if ('1.post_merger#'+binf+'b.DHHI_binsf' in did_merger.index):

                        aggregated['post_merger_'+binf+'.DHHIf'].append(did_merger['(5)']['1.post_merger#'+binf+'b.DHHI_binsf'])
                        aggregated['se_pm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger#'+binf+'b.DHHI_binsf')+1)])
                        aggregated['pv_pm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger#'+binf+'b.DHHI_binsf')+2)])

                    elif ('1.post_merger#'+binf+'.DHHI_binsf' in did_merger.index):

                        aggregated['post_merger_'+binf+'.DHHIf'].append(did_merger['(5)']['1.post_merger#'+binf+'.DHHI_binsf'])
                        aggregated['se_pm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger#'+binf+'.DHHI_binsf')+1)])
                        aggregated['pv_pm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger#'+binf+'.DHHI_binsf')+2)])

                else:

                    aggregated['post_merger_'+binf+'.DHHIf'].append(np.nan)
                    aggregated['se_pm'+binf+'.DHHIf'].append(np.nan)
                    aggregated['pv_pm'+binf+'.DHHIf'].append(np.nan)

            for binf in Finer_Bins:

                # post_merger_merging # i.DHHI finer bins
                if ('1.post_merger_merging#'+binf+'b.DHHI_binsf' in did_merger.index) or ('1.post_merger_merging#'+binf+'.DHHI_binsf' in did_merger.index):

                    if ('1.post_merger_merging#'+binf+'b.DHHI_binsf' in did_merger.index):

                        aggregated['post_merger_merging_'+binf+'.DHHIf'].append(did_merger['(5)']['1.post_merger_merging#'+binf+'b.DHHI_binsf'])
                        aggregated['se_pmm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'b.DHHI_binsf')+1)])
                        aggregated['pv_pmm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'b.DHHI_binsf')+2)])

                    elif ('1.post_merger_merging#'+binf+'.DHHI_binsf' in did_merger.index):

                        aggregated['post_merger_merging_'+binf+'.DHHIf'].append(did_merger['(5)']['1.post_merger#'+binf+'.DHHI_binsf'])
                        aggregated['se_pmm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'.DHHI_binsf')+1)])
                        aggregated['pv_pmm'+binf+'.DHHIf'].append(did_merger['(5)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'.DHHI_binsf')+2)])

                else:

                    aggregated['post_merger_merging_'+binf+'.DHHIf'].append(np.nan)
                    aggregated['se_pmm'+binf+'.DHHIf'].append(np.nan)
                    aggregated['pv_pmm'+binf+'.DHHIf'].append(np.nan)


            #Coefficients for DHHI_HHI bins
            for binf in Finer_Bins:

                # post_merger # i.DHHI_HHI bins
                if ('1.post_merger#'+binf+'b.DHHI_HHI' in did_merger.index) or ('1.post_merger#'+binf+'.DHHI_HHI' in did_merger.index):

                    if ('1.post_merger#'+binf+'b.DHHI_HHI' in did_merger.index):

                        aggregated['post_merger_'+binf+'.DHHI_HHI'].append(did_merger['(6)']['1.post_merger#'+binf+'b.DHHI_HHI'])
                        aggregated['se_pm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger#'+binf+'b.DHHI_HHI')+1)])
                        aggregated['pv_pm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger#'+binf+'b.DHHI_HHI')+2)])

                    elif ('1.post_merger#'+binf+'.DHHI_HHI' in did_merger.index):

                        aggregated['post_merger_'+binf+'.DHHI_HHI'].append(did_merger['(6)']['1.post_merger#'+binf+'.DHHI_HHI'])
                        aggregated['se_pm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger#'+binf+'.DHHI_HHI')+1)])
                        aggregated['pv_pm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger#'+binf+'.DHHI_HHI')+2)])

                else:

                    aggregated['post_merger_'+binf+'.DHHI_HHI'].append(np.nan)
                    aggregated['se_pm'+binf+'.DHHI_HHI'].append(np.nan)
                    aggregated['pv_pm'+binf+'.DHHI_HHI'].append(np.nan)


            for binf in Finer_Bins:

                # post_merger_merging # i.DHHI finer bins
                if ('1.post_merger_merging#'+binf+'b.DHHI_HHI' in did_merger.index) or ('1.post_merger_merging#'+binf+'.DHHI_HHI' in did_merger.index):

                    if ('1.post_merger_merging#'+binf+'b.DHHI_HHI' in did_merger.index):

                        aggregated['post_merger_merging_'+binf+'.DHHI_HHI'].append(did_merger['(6)']['1.post_merger_merging#'+binf+'b.DHHI_HHI'])
                        aggregated['se_pmm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'b.DHHI_HHI')+1)])
                        aggregated['pv_pmm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'b.DHHI_HHI')+2)])

                    elif ('1.post_merger_merging#'+binf+'.DHHI_HHI' in did_merger.index):

                        aggregated['post_merger_merging_'+binf+'.DHHI_HHI'].append(did_merger['(6)']['1.post_merger_merging#'+binf+'.DHHI_HHI'])
                        aggregated['se_pmm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'.DHHI_HHI')+1)])
                        aggregated['pv_pmm'+binf+'.DHHI_HHI'].append(did_merger['(6)'][(did_merger.index.get_loc('1.post_merger_merging#'+binf+'.DHHI_HHI')+2)])

                else:

                    aggregated['post_merger_merging_'+binf+'.DHHI_HHI'].append(np.nan)
                    aggregated['se_pmm'+binf+'.DHHI_HHI'].append(np.nan)
                    aggregated['pv_pmm'+binf+'.DHHI_HHI'].append(np.nan)

            #Coefficients for DHHI_HHI_NW bins
            for binc in Coarse_Bins:

                # post_merger # i.DHHI_HHI_NW bins
                if ('1.post_merger#'+binc+'b.DHHI_HHI_NW' in did_merger.index) or ('1.post_merger#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                    if ('1.post_merger#'+binc+'b.DHHI_HHI_NW' in did_merger.index):

                        aggregated['post_merger_'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)']['1.post_merger#'+binc+'b.DHHI_HHI_NW'])
                        aggregated['se_pm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger#'+binc+'b.DHHI_HHI_NW')+1)])
                        aggregated['pv_pm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger#'+binc+'b.DHHI_HHI_NW')+2)])

                    elif ('1.post_merger#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                        aggregated['post_merger_'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)']['1.post_merger#'+binc+'.DHHI_HHI_NW'])
                        aggregated['se_pm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger#'+binc+'.DHHI_HHI_NW')+1)])
                        aggregated['pv_pm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger#'+binc+'.DHHI_HHI_NW')+2)])

                else:

                    aggregated['post_merger_'+binc+'.DHHI_HHI_NW'].append(np.nan)
                    aggregated['se_pm'+binc+'.DHHI_HHI_NW'].append(np.nan)
                    aggregated['pv_pm'+binc+'.DHHI_HHI_NW'].append(np.nan)


            for binc in Coarse_Bins:

                # post_merger_merging # i.DHHI finer bins
                if ('1.post_merger_merging#'+binc+'b.DHHI_HHI_NW' in did_merger.index) or ('1.post_merger_merging#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                    if ('1.post_merger_merging#'+binc+'b.DHHI_HHI_NW' in did_merger.index):

                        aggregated['post_merger_merging_'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)']['1.post_merger_merging#'+binc+'b.DHHI_HHI_NW'])
                        aggregated['se_pmm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'b.DHHI_HHI_NW')+1)])
                        aggregated['pv_pmm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'b.DHHI_HHI_NW')+2)])

                    elif ('1.post_merger_merging#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                        aggregated['post_merger_merging_'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)']['1.post_merger_merging#'+binc+'.DHHI_HHI_NW'])
                        aggregated['se_pmm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'.DHHI_HHI_NW')+1)])
                        aggregated['pv_pmm'+binc+'.DHHI_HHI_NW'].append(did_merger['(7)'][(did_merger.index.get_loc('1.post_merger_merging#'+binc+'.DHHI_HHI_NW')+2)])

                else:

                    aggregated['post_merger_merging_'+binc+'.DHHI_HHI_NW'].append(np.nan)
                    aggregated['se_pmm'+binc+'.DHHI_HHI_NW'].append(np.nan)
                    aggregated['pv_pmm'+binc+'.DHHI_HHI_NW'].append(np.nan)

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df = df.dropna(axis=1, how='all')
    df = aux.clean_betas(df)
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.rstrip('*')
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.replace(',', '')
    df[df.columns[1]] = pd.to_numeric(df[df.columns[1]])
    df.to_csv('output/did_bins_agg.csv', sep=',')


# level is either "brandlevel_" or ""
level = sys.argv[1] + '_'

base_folder = '../../../All/'

#problematic codes
codes = (['m_1785984020_11', 'm_2664559020_1', 'm_2735179020_1', 'm_2735179020_4',
        'm_2736521020_10', 'm_2033113020_1_OLD', 'm_2033113020_2',
        'm_2675324040_1', 'm_2033113020_3', 'm_2838188020_1',
        'm_2033113020_3_OLD', 'm_2033113020_2_OLD', 'm_m_2203820020_6',
        'm_2813860020_1'])

log_out = open('output/agg_bins.log', 'w')
log_err = open('output/agg_bins.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

folders = [folder for folder in os.listdir(base_folder) if folder not in codes]

get_betas(folders, base_folder, level)
