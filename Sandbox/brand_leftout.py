import re
import os
import pandas as pd
import sys
import numpy as np

def parse_info(file):

    file = open(file, mode='r')
    info_file = file.read()
    file.close()

    all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
    info_dict = {}

    for info in all_info_elements:

        info_name = info.group(1).strip()
        info_content = info.group(2).strip()
        info_dict[info_name] = info_content

    return info_dict

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
    N_parties = overlap_file.shape[0]

    if merging_sum < 2:
        return (False, c4, tot_sales, merging_sum, N_parties)

    elif merging_sum == 3:
        return (True, c4, tot_sales, merging_sum, N_parties)

    elif merging_sum == 2:

        df_merging = overlap_file[overlap_file['merging_party'] == 1]

        if ((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0)):
            return (False, c4, tot_sales, merging_sum, N_parties)

        else:
            return (True, c4, tot_sales, merging_sum, N_parties)

def get_stats(base_folder):

    folders = [folder for folder in os.listdir(base_folder)]

    aggregated = {}
    aggregated['merger']       = []
    aggregated['deal']         = []
    aggregated['brand_upc']    = []
    aggregated['share_upc']    = []
    aggregated['brand_brand']  = []
    aggregated['share_brand']  = []
    aggregated['descr']        = []
    aggregated['overlap']      = []
    aggregated['c4']           = []
    aggregated['tot_sales']    = []
    aggregated['n_parties']    = []
    aggregated['N_of_parties'] = []

    for folder in folders:

        data_path = base_folder + folder + '/intermediate/'
        infotxt   = base_folder + folder + '/info.txt'
        output    = base_folder + folder + '/output'

        print(data_path)

        if os.path.exists(data_path + 'market_coverage_brandlevel.csv'):

            info = parse_info(infotxt)

            aggregated['merger'].append(folder)
            aggregated['descr'].append(info['Summary'])
            aggregated['deal'].append(folder.split('_')[1])
            print(folder)

            df1 = pd.read_csv(data_path + 'market_coverage.csv', sep=',')
            brand1 = df1.loc[df1.share_of_largest_brand_left_out.idxmax(), ['largest_brand_left_out']][0]
            share1 = df1['share_of_largest_brand_left_out'].max()
            df2 = pd.read_csv(data_path + 'market_coverage_brandlevel.csv', sep=',')
            brand2 = df2.loc[df2.share_of_largest_brand_left_out.idxmax(), ['largest_brand_left_out']][0]
            share2 = df2['share_of_largest_brand_left_out'].max()

            overlap = check_overlap(output)[0]
            c4 = check_overlap(output)[1]
            tot_sales = check_overlap(output)[2]
            n_of_mparties = check_overlap(output)[3]
            N_of_parties = check_overlap(output)[4]

            aggregated['overlap'].append(overlap)
            aggregated['c4'].append(c4)
            aggregated['tot_sales'].append(tot_sales)
            aggregated['n_parties'].append(n_of_mparties)
            aggregated['N_of_parties'].append(N_of_parties)

            aggregated['brand_upc'].append(brand1)
            aggregated['share_upc'].append(share1)
            aggregated['brand_brand'].append(brand2)
            aggregated['share_brand'].append(share2)

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df.to_csv('output/brand_leftout.csv', sep=',')


base_folder = '../../../All/'

log_out = open('output/brand_leftout.log', 'w')
log_err = open('output/brand_leftout.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

get_stats(base_folder)
