
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
    tot_sales = overlap_file['pre_sales'].sum()

    if merging_sum < 2:
        return (False, c4, tot_sales)

    elif merging_sum == 3:
        return (True, c4, tot_sales)

    elif merging_sum == 2:

        df_merging = overlap_file[overlap_file['merging_party'] == 1]

        if ((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0)):
            return (False, c4, tot_sales)

        else:
            return (True, c4, tot_sales)


def get_betas(folders, base_folder):

    '''
    At the base_folder, it loops through all m_code folders,
    checks whether the brand_level routine is done, and retrieves
    the coefficients, standard erros, and p-values of that routine.
    It generates the "output/aggregated_brand.csv" file.
    '''

    # Dictionary with the descriptive variables
    aggregated = {}
    aggregated['merger'] = []
    aggregated['tot_sales'] = []

    # Adding all the specs-vars to the Dictionary
    for i in range(48):

        j = i+1

        Coarse_Bins = ['0', '1', '2']
        for binc in Coarse_Bins:
            aggregated['Post_Merging_'+binc+'.HHI_'+str(j)] = []
            aggregated['se_pmm'+binc+'.HHI_'+str(j)] = []
            aggregated['pv_pmm'+binc+'.HHI_'+str(j)] = []
            aggregated['Post_Non_Merging_'+binc+'.HHI_'+str(j)] = []
            aggregated['se_pnm'+binc+'.HHI_'+str(j)] = []
            aggregated['pv_pnm'+binc+'.HHI_'+str(j)] = []

            aggregated['Post_Merging_'+binc+'.DHHI_'+str(j)] = []
            aggregated['se_pmm'+binc+'.DHHI_'+str(j)] = []
            aggregated['pv_pmm'+binc+'.DHHI_'+str(j)] = []
            aggregated['Post_Non_Merging_'+binc+'.DHHI_'+str(j)] = []
            aggregated['se_pnm'+binc+'.DHHI_'+str(j)] = []
            aggregated['pv_pnm'+binc+'.DHHI_'+str(j)] = []

            aggregated['Post_Merging_'+binc+'.DHHI_HHI_NW_'+str(j)] = []
            aggregated['se_pmm'+binc+'.DHHI_HHI_NW_'+str(j)] = []
            aggregated['pv_pmm'+binc+'.DHHI_HHI_NW_'+str(j)] = []
            aggregated['Post_Non_Merging_'+binc+'.DHHI_HHI_NW_'+str(j)] = []
            aggregated['se_pnm'+binc+'.DHHI_HHI_NW_'+str(j)] = []
            aggregated['pv_pnm'+binc+'.DHHI_HHI_NW_'+str(j)] = []

        Finer_Bins = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
        for binc in Finer_Bins:
            aggregated['Post_Merging_'+binc+'.HHIf_'+str(j)] = []
            aggregated['se_pmm'+binc+'.HHIf_'+str(j)] = []
            aggregated['pv_pmm'+binc+'.HHIf_'+str(j)] = []
            aggregated['Post_Non_Merging_'+binc+'.HHIf_'+str(j)] = []
            aggregated['se_pnm'+binc+'.HHIf_'+str(j)] = []
            aggregated['pv_pnm'+binc+'.HHIf_'+str(j)] = []

            aggregated['Post_Merging_'+binc+'.DHHIf_'+str(j)] = []
            aggregated['se_pmm'+binc+'.DHHIf_'+str(j)] = []
            aggregated['pv_pmm'+binc+'.DHHIf_'+str(j)] = []
            aggregated['Post_Non_Merging_'+binc+'.DHHIf_'+str(j)] = []
            aggregated['se_pnm'+binc+'.DHHIf_'+str(j)] = []
            aggregated['pv_pnm'+binc+'.DHHIf_'+str(j)] = []

            aggregated['Post_Merging_'+binc+'.DHHI_HHI_'+str(j)] = []
            aggregated['se_pmm'+binc+'.DHHI_HHI_'+str(j)] = []
            aggregated['pv_pmm'+binc+'.DHHI_HHI_'+str(j)] = []
            aggregated['Post_Non_Merging_'+binc+'.DHHI_HHI_'+str(j)] = []
            aggregated['se_pnm'+binc+'.DHHI_HHI_'+str(j)] = []
            aggregated['pv_pnm'+binc+'.DHHI_HHI_'+str(j)] = []

        for month in range(49):
            month = month + 1
            aggregated['Merging_'+str(month) + '.Months_'+str(j)] = []
            aggregated['se_M_'+str(month) + '.Months_'+str(j)] = []
            aggregated['pv_M_'+str(month) + '.Months_'+str(j)] = []

            aggregated['Non_Merging_'+str(month) + '.Months_'+str(j)] = []
            aggregated['se_NM_'+str(month) + '.Months_'+str(j)] = []
            aggregated['pv_NM_'+str(month) + '.Months_'+str(j)] = []


        coefficients = ['Merging_Treated_2', 'Merging_Treated_5', 'Merging_Treated_10', 'Non_Merging_Treated_2',
                        'Non_Merging_Treated_5', 'Non_Merging_Treated_10', 'Merging_Treated_Post_2', 'Merging_Treated_Post_5',
                        'Merging_Treated_Post_10', 'Non_Merging_Treated_Post_2', 'Non_Merging_Treated_Post_5', 'Non_Merging_Treated_Post_10',
                        'Merging', 'Post_Merging', 'Post_Non_Merging', 'Major', 'Post_Major', 'Post_Minor', 'Post_Merging_1y', 'Post_Non_Merging_1y',
                        'Post_Merging', 'post_merger', 'Treated_2', 'Treated_5', 'Treated_10', 'Treated_Post_2', 'Treated_Post_5', 'Treated_Post_10']

        for coef in coefficients:
            aggregated[coef+'_'+str(j)] = []
            aggregated['se_'+coef+'_'+str(j)] = []
            aggregated['pv_'+coef+'_'+str(j)] = []


    # print(aggregated)

    # loop through folders in "All"
    #folders = [folder for folder in os.listdir(base_folder) if folder not in codes]
    #print(folders)
    for folder in folders:

        merger_folder = base_folder + folder + '/output'
        data_folder = base_folder + folder + '/intermediate'
        # go inside folders with step5 finished
        if os.path.exists(merger_folder + '/did_int_lprice_2.txt'):

            read_file = pd.read_csv(merger_folder + "/did_int_lprice_2.txt", sep="\t")
            read_file = read_file.replace(np.nan, '', regex=True)
            read_file.to_csv(merger_folder + "/did_int_lprice_2.csv", index=None)

            did_merger = pd.read_csv(merger_folder + '/did_int_lprice_2.csv', sep=',')
            did_merger.index = did_merger['Unnamed: 0']

            print(folder)

            # append the m_folder name and descriptive stats to the dictionary
            aggregated['merger'].append(folder)
            aggregated['tot_sales'].append(check_overlap(merger_folder)[2])

            for col in did_merger.columns[1:]:
            #Coefficients for HHI Coarse Bins
                col2 = col.lstrip('(').rstrip(')')
                for binc in Coarse_Bins:

                    #Coefficients for Post_Non_Merging # i.HHI Coarse Bins
                    if ('1.Post_Non_Merging#'+binc+'b.HHI_bins' in did_merger.index) or ('1.Post_Non_Merging#'+binc+'.HHI_bins' in did_merger.index):

                        if ('1.Post_Non_Merging#'+binc+'b.HHI_bins' in did_merger.index):

                            # loop through specs recovering betas
                            aggregated['Post_Non_Merging_'+binc+'.HHI_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binc+'b.HHI_bins'])
                            aggregated['se_pnm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'b.HHI_bins')+1)])
                            aggregated['pv_pnm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'b.HHI_bins')+2)])

                        elif ('1.Post_Non_Merging#'+binc+'.HHI_bins' in did_merger.index):

                           # loop through specs recovering betas
                            aggregated['Post_Non_Merging_'+binc+'.HHI_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binc+'.HHI_bins'])
                            aggregated['se_pnm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'.HHI_bins')+1)])
                            aggregated['pv_pnm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'.HHI_bins')+2)])

                    else:

                        aggregated['Post_Non_Merging_'+binc+'.HHI_' + col2].append(np.nan)
                        aggregated['se_pnm'+binc+'.HHI_' + col2].append(np.nan)
                        aggregated['pv_pnm'+binc+'.HHI_' + col2].append(np.nan)

                for binc in Coarse_Bins:

                    #Coefficients for Post_Merging # i.HHI coarse bins
                    if ('1.Post_Merging#'+binc+'b.HHI_bins' in did_merger.index) or ('1.Post_Merging#'+binc+'.HHI_bins' in did_merger.index):

                        if ('1.Post_Merging#'+binc+'b.HHI_bins' in did_merger.index):

                            # loop through specs recovering betas
                            aggregated['Post_Merging_'+binc+'.HHI_' + col2].append(did_merger[col]['1.Post_Merging#'+binc+'b.HHI_bins'])
                            aggregated['se_pmm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'b.HHI_bins')+1)])
                            aggregated['pv_pmm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'b.HHI_bins')+2)])

                        elif ('1.Post_Merging#'+binc+'.HHI_bins' in did_merger.index):

                           # loop through specs recovering betas
                            aggregated['Post_Merging_'+binc+'.HHI_' + col2].append(did_merger[col]['1.Post_Merging#'+binc+'.HHI_bins'])
                            aggregated['se_pmm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'.HHI_bins')+1)])
                            aggregated['pv_pmm'+binc+'.HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'.HHI_bins')+2)])

                    else:

                        aggregated['Post_Merging_'+binc+'.HHI_' + col2].append(np.nan)
                        aggregated['se_pmm'+binc+'.HHI_' + col2].append(np.nan)
                        aggregated['pv_pmm'+binc+'.HHI_' + col2].append(np.nan)

                # Coefficients for DHHI Coarse Bins
                for binc in Coarse_Bins:

                    #Post_Non_Merging # i.DHHI coarse bins
                    if ('1.Post_Non_Merging#'+binc+'b.DHHI_bins' in did_merger.index) or ('1.Post_Non_Merging#'+binc+'.DHHI_bins' in did_merger.index):

                        if ('1.Post_Non_Merging#'+binc+'b.DHHI_bins' in did_merger.index):

                            # loop through specs recovering betas
                            aggregated['Post_Non_Merging_'+binc+'.DHHI_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binc+'b.DHHI_bins'])
                            aggregated['se_pnm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'b.DHHI_bins')+1)])
                            aggregated['pv_pnm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'b.DHHI_bins')+2)])

                        elif ('1.Post_Non_Merging#'+binc+'.DHHI_bins' in did_merger.index):

                           # loop through specs recovering betas
                            aggregated['Post_Non_Merging_'+binc+'.DHHI_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binc+'.DHHI_bins'])
                            aggregated['se_pnm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'.DHHI_bins')+1)])
                            aggregated['pv_pnm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'.DHHI_bins')+2)])

                    else:

                        aggregated['Post_Non_Merging_'+binc+'.DHHI_' + col2].append(np.nan)
                        aggregated['se_pnm'+binc+'.DHHI_' + col2].append(np.nan)
                        aggregated['pv_pnm'+binc+'.DHHI_' + col2].append(np.nan)

                for binc in Coarse_Bins:

                    # Post_Merging # i.DHHI coarse bins
                    if ('1.Post_Merging#'+binc+'b.DHHI_bins' in did_merger.index) or ('1.Post_Merging#'+binc+'.DHHI_bins' in did_merger.index):

                        if ('1.Post_Non_Merging#'+binc+'b.DHHI_bins' in did_merger.index):

                            # loop through specs recovering betas
                            aggregated['Post_Merging_'+binc+'.DHHI_' + col2].append(did_merger[col]['1.Post_Merging#'+binc+'b.DHHI_bins'])
                            aggregated['se_pmm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'b.DHHI_bins')+1)])
                            aggregated['pv_pmm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'b.DHHI_bins')+2)])

                        elif ('1.Post_Merging#'+binc+'.DHHI_bins' in did_merger.index):

                           # loop through specs recovering betas
                            aggregated['Post_Merging_'+binc+'.DHHI_' + col2].append(did_merger[col]['1.Post_Merging#'+binc+'.DHHI_bins'])
                            aggregated['se_pmm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'.DHHI_bins')+1)])
                            aggregated['pv_pmm'+binc+'.DHHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'.DHHI_bins')+2)])

                    else:

                        aggregated['Post_Merging_'+binc+'.DHHI_' + col2].append(np.nan)
                        aggregated['se_pmm'+binc+'.DHHI_' + col2].append(np.nan)
                        aggregated['pv_pmm'+binc+'.DHHI_' + col2].append(np.nan)

                # Coefficients for HHI Finer Bins
                for binf in Finer_Bins:

                    # Post_Non_Merging # i.HHI fine bins
                    if ('1.Post_Non_Merging#'+binf+'b.HHI_binsf' in did_merger.index) or ('1.Post_Non_Merging#'+binf+'.HHI_binsf' in did_merger.index):

                        if ('1.Post_Non_Merging#'+binf+'b.HHI_binsf' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binf+'.HHIf_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binf+'b.HHI_binsf'])
                            aggregated['se_pnm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'b.HHI_binsf')+1)])
                            aggregated['pv_pnm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'b.HHI_binsf')+2)])

                        elif ('1.Post_Non_Merging#'+binf+'.HHI_binsf' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binf+'.HHIf_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binf+'.HHI_binsf'])
                            aggregated['se_pnm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'.HHI_binsf')+1)])
                            aggregated['pv_pnm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'.HHI_binsf')+2)])

                    else:

                        aggregated['Post_Non_Merging_'+binf+'.HHIf_' + col2].append(np.nan)
                        aggregated['se_pnm'+binf+'.HHIf_' + col2].append(np.nan)
                        aggregated['pv_pnm'+binf+'.HHIf_' + col2].append(np.nan)

                for binf in Finer_Bins:

                    # Post_Merging # i.HHI fine bins
                    if ('1.Post_Merging#'+binf+'b.HHI_binsf' in did_merger.index) or ('1.Post_Merging#'+binf+'.HHI_binsf' in did_merger.index):

                        if ('1.Post_Merging#'+binf+'b.HHI_binsf' in did_merger.index):

                            aggregated['Post_Merging_'+binf+'.HHIf_' + col2].append(did_merger[col]['1.Post_Merging#'+binf+'b.HHI_binsf'])
                            aggregated['se_pmm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'b.HHI_binsf')+1)])
                            aggregated['pv_pmm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'b.HHI_binsf')+2)])

                        elif ('1.Post_Merging#'+binf+'.HHI_binsf' in did_merger.index):

                            aggregated['Post_Merging_'+binf+'.HHIf_' + col2].append(did_merger[col]['1.Post_Merging#'+binf+'.HHI_binsf'])
                            aggregated['se_pmm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'.HHI_binsf')+1)])
                            aggregated['pv_pmm'+binf+'.HHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'.HHI_binsf')+2)])

                    else:

                        aggregated['Post_Merging_'+binf+'.HHIf_' + col2].append(np.nan)
                        aggregated['se_pmm'+binf+'.HHIf_' + col2].append(np.nan)
                        aggregated['pv_pmm'+binf+'.HHIf_' + col2].append(np.nan)

                # Coefficients for DHHI Finer Bins
                for binf in Finer_Bins:

                    # Post_Non_Merging # i.DHHI fine bins
                    if ('1.Post_Non_Merging#'+binf+'b.DHHI_binsf' in did_merger.index) or ('1.Post_Non_Merging#'+binf+'.DHHI_binsf' in did_merger.index):

                        if ('1.Post_Non_Merging#'+binf+'b.DHHI_binsf' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binf+'.DHHIf_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binf+'b.DHHI_binsf'])
                            aggregated['se_pnm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'b.DHHI_binsf')+1)])
                            aggregated['pv_pnm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'b.DHHI_binsf')+2)])

                        elif ('1.Post_Non_Merging#'+binf+'.DHHI_binsf' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binf+'.DHHIf_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binf+'.DHHI_binsf'])
                            aggregated['se_pnm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'.DHHI_binsf')+1)])
                            aggregated['pv_pnm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'.DHHI_binsf')+2)])

                    else:

                        aggregated['Post_Non_Merging_'+binf+'.DHHIf_' + col2].append(np.nan)
                        aggregated['se_pnm'+binf+'.DHHIf_' + col2].append(np.nan)
                        aggregated['pv_pnm'+binf+'.DHHIf_' + col2].append(np.nan)

                for binf in Finer_Bins:

                    # Post_Merging # i.DHHI finer bins
                    if ('1.Post_Merging#'+binf+'b.DHHI_binsf' in did_merger.index) or ('1.Post_Merging#'+binf+'.DHHI_binsf' in did_merger.index):

                        if ('1.Post_Merging#'+binf+'b.DHHI_binsf' in did_merger.index):

                            aggregated['Post_Merging_'+binf+'.DHHIf_' + col2].append(did_merger[col]['1.Post_Merging#'+binf+'b.DHHI_binsf'])
                            aggregated['se_pmm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'b.DHHI_binsf')+1)])
                            aggregated['pv_pmm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'b.DHHI_binsf')+2)])

                        elif ('1.Post_Merging#'+binf+'.DHHI_binsf' in did_merger.index):

                            aggregated['Post_Merging_'+binf+'.DHHIf_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binf+'.DHHI_binsf'])
                            aggregated['se_pmm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'.DHHI_binsf')+1)])
                            aggregated['pv_pmm'+binf+'.DHHIf_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'.DHHI_binsf')+2)])

                    else:

                        aggregated['Post_Merging_'+binf+'.DHHIf_' + col2].append(np.nan)
                        aggregated['se_pmm'+binf+'.DHHIf_' + col2].append(np.nan)
                        aggregated['pv_pmm'+binf+'.DHHIf_' + col2].append(np.nan)

                # Coefficients for DHHI_HHI bins
                for binf in Finer_Bins:

                    # Post_Non_Merging # i.DHHI_HHI bins
                    if ('1.Post_Non_Merging#'+binf+'b.DHHI_HHI' in did_merger.index) or ('1.Post_Non_Merging#'+binf+'.DHHI_HHI' in did_merger.index):

                        if ('1.Post_Non_Merging#'+binf+'b.DHHI_HHI' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binf+'.DHHI_HHI_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binf+'b.DHHI_HHI'])
                            aggregated['se_pnm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'b.DHHI_HHI')+1)])
                            aggregated['pv_pnm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'b.DHHI_HHI')+2)])

                        elif ('1.Post_Non_Merging#'+binf+'.DHHI_HHI' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binf+'.DHHI_HHI_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binf+'.DHHI_HHI'])
                            aggregated['se_pnm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'.DHHI_HHI')+1)])
                            aggregated['pv_pnm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binf+'.DHHI_HHI')+2)])

                    else:

                        aggregated['Post_Non_Merging_'+binf+'.DHHI_HHI_' + col2].append(np.nan)
                        aggregated['se_pnm'+binf+'.DHHI_HHI_' + col2].append(np.nan)
                        aggregated['pv_pnm'+binf+'.DHHI_HHI_' + col2].append(np.nan)

                for binf in Finer_Bins:

                    # Post_Merging # i.DHHI finer bins
                    if ('1.Post_Merging#'+binf+'b.DHHI_HHI' in did_merger.index) or ('1.Post_Merging#'+binf+'.DHHI_HHI' in did_merger.index):

                        if ('1.Post_Merging#'+binf+'b.DHHI_HHI' in did_merger.index):

                            aggregated['Post_Merging_'+binf+'.DHHI_HHI_' + col2].append(did_merger[col]['1.Post_Merging#'+binf+'b.DHHI_HHI'])
                            aggregated['se_pmm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'b.DHHI_HHI')+1)])
                            aggregated['pv_pmm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'b.DHHI_HHI')+2)])

                        elif ('1.Post_Merging#'+binf+'.DHHI_HHI' in did_merger.index):

                            aggregated['Post_Merging_'+binf+'.DHHI_HHI_' + col2].append(did_merger[col]['1.Post_Merging#'+binf+'.DHHI_HHI'])
                            aggregated['se_pmm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'.DHHI_HHI')+1)])
                            aggregated['pv_pmm'+binf+'.DHHI_HHI_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binf+'.DHHI_HHI')+2)])

                    else:

                        aggregated['Post_Merging_'+binf+'.DHHI_HHI_' + col2].append(np.nan)
                        aggregated['se_pmm'+binf+'.DHHI_HHI_' + col2].append(np.nan)
                        aggregated['pv_pmm'+binf+'.DHHI_HHI_' + col2].append(np.nan)

                # Coefficients for DHHI_HHI_NW bins
                for binc in Coarse_Bins:

                    # Post_Non_Merging # i.DHHI_HHI_NW bins
                    if ('1.Post_Non_Merging#'+binc+'b.DHHI_HHI_NW' in did_merger.index) or ('1.Post_Non_Merging#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                        if ('1.Post_Non_Merging#'+binc+'b.DHHI_HHI_NW' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binc+'b.DHHI_HHI_NW'])
                            aggregated['se_pnm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'b.DHHI_HHI_NW')+1)])
                            aggregated['pv_pnm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'b.DHHI_HHI_NW')+2)])

                        elif ('1.Post_Non_Merging#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                            aggregated['Post_Non_Merging_'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col]['1.Post_Non_Merging#'+binc+'.DHHI_HHI_NW'])
                            aggregated['se_pnm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'.DHHI_HHI_NW')+1)])
                            aggregated['pv_pnm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Non_Merging#'+binc+'.DHHI_HHI_NW')+2)])

                    else:

                        aggregated['Post_Non_Merging_'+binc+'.DHHI_HHI_NW_' + col2].append(np.nan)
                        aggregated['se_pnm'+binc+'.DHHI_HHI_NW_' + col2].append(np.nan)
                        aggregated['pv_pnm'+binc+'.DHHI_HHI_NW_' + col2].append(np.nan)

                for binc in Coarse_Bins:

                    # Post_Merging # i.DHHI finer bins
                    if ('1.Post_Merging#'+binc+'b.DHHI_HHI_NW' in did_merger.index) or ('1.Post_Merging#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                        if ('1.Post_Merging#'+binc+'b.DHHI_HHI_NW' in did_merger.index):

                            aggregated['Post_Merging_'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col]['1.Post_Merging#'+binc+'b.DHHI_HHI_NW'])
                            aggregated['se_pmm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'b.DHHI_HHI_NW')+1)])
                            aggregated['pv_pmm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'b.DHHI_HHI_NW')+2)])

                        elif ('1.Post_Merging#'+binc+'.DHHI_HHI_NW' in did_merger.index):

                            aggregated['Post_Merging_'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col]['1.Post_Merging#'+binc+'.DHHI_HHI_NW'])
                            aggregated['se_pmm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'.DHHI_HHI_NW')+1)])
                            aggregated['pv_pmm'+binc+'.DHHI_HHI_NW_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Post_Merging#'+binc+'.DHHI_HHI_NW')+2)])

                    else:

                        aggregated['Post_Merging_'+binc+'.DHHI_HHI_NW_' + col2].append(np.nan)
                        aggregated['se_pmm'+binc+'.DHHI_HHI_NW_' + col2].append(np.nan)
                        aggregated['pv_pmm'+binc+'.DHHI_HHI_NW_' + col2].append(np.nan)

                for month in range(49):
                    month = str(month + 1)

                    # Merging # Months Post
                    if ('1.Merging#'+str(month)+'b.Months' in did_merger.index) or ('1.Merging#'+str(month)+'.Months' in did_merger.index):

                        if ('1.Merging#'+month+'b.Months' in did_merger.index):

                            aggregated['Merging_'+str(month) + '.Months_' + col2].append(did_merger[col]['1.erging#'+month+'b.Months'])
                            aggregated['se_M_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'b.Months')+1)])
                            aggregated['pv_M_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'b.Months')+2)])

                        elif ('1.Merging#'+month+'.Months' in did_merger.index):

                            aggregated['Merging_'+str(month) + '.Months_' + col2].append(did_merger[col]['1.Merging#'+month+'.Months'])
                            aggregated['se_M_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'.Months')+1)])
                            aggregated['pv_M_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'.Months')+2)])

                    else:

                        aggregated['Merging_'+str(month) + '.Months_' + col2].append(np.nan)
                        aggregated['se_M_'+str(month) + '.Months_' + col2].append(np.nan)
                        aggregated['pv_M_'+str(month) + '.Months_' + col2].append(np.nan)

                    if ('1.Non_Merging#'+str(month)+'b.Months' in did_merger.index) or ('1.Non_Merging#'+str(month)+'.Months' in did_merger.index):

                        if ('1.Non_Merging#'+month+'b.Months' in did_merger.index):

                            aggregated['Non_Merging_'+str(month) + '.Months_' + col2].append(did_merger[col]['1.Non_Merging#'+month+'b.Months'])
                            aggregated['se_NM_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'b.Months')+1)])
                            aggregated['pv_NM_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'b.Months')+2)])

                        elif ('1.Post_Non_Merging#'+month+'.Months' in did_merger.index):

                            aggregated['Non_Merging_'+str(month) + '.Months_' + col2].append(did_merger[col]['1.Non_Merging#'+month+'.Months_post'])
                            aggregated['se_NM_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'.Months')+1)])
                            aggregated['pv_NM_'+str(month) + '.Months_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'.Months')+2)])

                    else:

                        aggregated['Non_Merging_'+str(month) + '.Months_' + col2].append(np.nan)
                        aggregated['se_NM_'+str(month) + '.Months_' + col2].append(np.nan)
                        aggregated['pv_NM_'+str(month) + '.Months_' + col2].append(np.nan)

                for month in range(24):
                    month = str(month + 1)

                    # Merging # Months Pre
                    if ('1.Merging#'+str(month)+'b.Months_pre' in did_merger.index) or ('1.Merging#'+str(month)+'.Months_pre' in did_merger.index):

                        if ('1.Merging#'+month+'b.Months_pre' in did_merger.index):

                            aggregated['Merging_'+str(month) + '.Months_pre_' + col2].append(did_merger[col]['1.Merging#'+month+'b.Months_pre'])
                            aggregated['se_M_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'b.Months_pre')+1)])
                            aggregated['pv_M_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'b.Months_pre')+2)])

                        elif ('1.Merging#'+month+'.Months_pre' in did_merger.index):

                            aggregated['Merging_'+str(month) + '.Months_pre_' + col2].append(did_merger[col]['1.Merging#'+month+'.Months_pre'])
                            aggregated['se_M_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'.Months_pre')+1)])
                            aggregated['pv_M_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Merging#'+month+'.Months_pre')+2)])

                    else:

                        aggregated['Merging_'+str(month) + '.Months_pre_' + col2].append(np.nan)
                        aggregated['se_M_'+str(month) + '.Months_pre_' + col2].append(np.nan)
                        aggregated['pv_M_'+str(month) + '.Months_pre_' + col2].append(np.nan)

                    # Non Merging # Months Pre
                    if ('1.Non_Merging#'+str(month)+'b.Months_pre' in did_merger.index) or ('1.Non_Merging#'+str(month)+'.Months_pre' in did_merger.index):

                        if ('1.Non_Merging#'+month+'b.Months_pre' in did_merger.index):

                            aggregated['Non_Merging_'+str(month) + '.Months_pre_' + col2].append(did_merger[col]['1.Non_Merging#'+month+'b.Months_pre'])
                            aggregated['se_NM_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'b.Months_pre')+1)])
                            aggregated['pv_NM_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'b.Months_pre')+2)])

                        elif ('1.Non_Merging#'+month+'.Months_pre' in did_merger.index):

                            aggregated['Non_Merging_'+str(month) + '.Months_pre_' + col2].append(did_merger[col]['1.Non_Merging#'+month+'.Months_pre'])
                            aggregated['se_NM_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'.Months_pre')+1)])
                            aggregated['pv_NM_'+str(month) + '.Months_pre_' + col2].append(did_merger[col][(did_merger.index.get_loc('1.Non_Merging#'+month+'.Months_pre')+2)])

                    else:

                        aggregated['Non_Merging_'+str(month) + '.Months_pre_' + col2].append(np.nan)
                        aggregated['se_NM_'+str(month) + '.Months_pre_' + col2].append(np.nan)
                        aggregated['pv_NM_'+str(month) + '.Months_pre_' + col2].append(np.nan)

                coefficients = ['Merging_Treated_2', 'Merging_Treated_5', 'Merging_Treated_10', 'Non_Merging_Treated_2',
                                'Non_Merging_Treated_5', 'Non_Merging_Treated_10', 'Merging_Treated_Post_2', 'Merging_Treated_Post_5',
                                'Merging_Treated_Post_10', 'Non_Merging_Treated_Post_2', 'Non_Merging_Treated_Post_5', 'Non_Merging_Treated_Post_10',
                                'Merging', 'Post_Merging', 'Post_Non_Merging', 'Major', 'Post_Major', 'Post_Minor', 'Post_Merging_1y', 'Post_Non_Merging_1y',
                                'Post_Merging', 'post_merger', 'Treated_2', 'Treated_5', 'Treated_10', 'Treated_Post_2', 'Treated_Post_5', 'Treated_Post_10']

                for coef in coefficients:

                    if (coef in did_merger.index):

                        aggregated[coef + '_' + col2].append(did_merger[col][coef])
                        aggregated['se_'+coef+'_'+col2].append(did_merger[col][(did_merger.index.get_loc(coef)+1)])
                        aggregated['pv_'+coef+'_'+col2].append(did_merger[col][(did_merger.index.get_loc(coef)+2)])

                    else:

                        aggregated[coef + '_' + col2].append(np.nan)
                        aggregated['se_'+coef+'_'+col2].append(np.nan)
                        aggregated['pv_'+coef+'_'+col2].append(np.nan)

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df = df.dropna(axis=1, how='all')
    df = aux.clean_betas(df)
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.rstrip('*')
    df[df.columns[1]] = df[df.columns[1]].astype(str).str.replace(',', '')
    df[df.columns[1]] = pd.to_numeric(df[df.columns[1]])
    df.to_csv('output/did_agg2.csv', sep=',')


# level is either "brandlevel_" or ""

base_folder = '../../../All/'

# problematic codes
codes = (['m_1785984020_11', 'm_2664559020_1', 'm_2735179020_1',
          'm_2735179020_4', 'm_2736521020_10', 'm_2033113020_1_OLD',
          'm_2033113020_2', 'm_2675324040_1', 'm_2033113020_3',
          'm_2838188020_1', 'm_2033113020_3_OLD', 'm_2033113020_2_OLD',
          'm_m_2203820020_6', 'm_2813860020_1'])

log_out = open('output/agg_bins2.log', 'w')
log_err = open('output/agg_bins2.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

folders = [folder for folder in os.listdir(base_folder) if folder not in codes]

get_betas(folders, base_folder)
