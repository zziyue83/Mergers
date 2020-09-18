
import re
import os
import pandas as pd
import auxiliary as aux
import numpy as np
import sys


def sum_parties(df, value):
    value = int(value)
    return len(df[df['mean'] == value])

def check_overlap(overlap_folder):

    overlap_file = pd.read_csv(overlap_folder + '/overlap.csv', sep=',')
    merging_sum = overlap_file['merging_party'].sum()

    if merging_sum < 2:
        return False

    elif merging_sum == 3:
        return True

    elif merging_sum == 2:

        df_merging = overlap_file[overlap_file['merging_party'] == 1]

        if (((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0))):
            return False

        else:
            return True

def counts(base_folder):

    # basic specs
    aggregated = {}
    aggregated['merger'] = []
    aggregated['parties_0'] = []
    aggregated['parties_1'] = []
    aggregated['parties_2'] = []
#    aggregated['parties_3'] = []
    aggregated['overlap'] = []

    # loop through folders in "All"
    for folder in os.listdir(base_folder):

        print(folder)
        merger_folder = base_folder + folder + '/intermediate'
        overlap_folder = base_folder + folder + '/output'
        # go inside folders with step9 finished
        if os.path.exists(merger_folder + '/stata_did_month.csv'):

            print(overlap_folder)
            did_file = pd.read_csv(merger_folder + "/stata_did_month.csv",
                                    sep=",")
            did_file.loc[did_file['merging'] == True, 'merg'] = int(1)
            did_file.loc[did_file['merging'] == False, 'merg'] = int(0)
            did_file = did_file[did_file['post_merger'] == 0] # new line
            did_grouped = did_file.groupby(['owner', 'dma_code'])['merg'].agg(['mean'])
            final_data = did_grouped.groupby(['dma_code']).sum()

            (aggregated['merger'].append(folder))
            (aggregated['parties_0'].
                    append(sum_parties(final_data, 0)))
            (aggregated['parties_1'].
                    append(sum_parties(final_data, 1)))
            (aggregated['parties_2'].
                    append(sum_parties(final_data, 2)))
            # (aggregated['parties_3'].
            #        append(sum_parties(final_data, 3)))
            (aggregated['overlap'].
                    append(check_overlap(overlap_folder)))

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df.to_csv('Parties_Count.csv', sep=',')


base_folder = '../../../All/'

log_out = open('output/Parties_Count.log', 'w')
log_err = open('output/Parties_Count.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

base_folder = '../../../All/'

counts(base_folder)


