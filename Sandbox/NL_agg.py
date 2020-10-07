
from matplotlib import pyplot as plt
import re
import os
import pandas as pd
import auxiliary as aux
import numpy as np
import sys
import seaborn as sns
import array_to_latex as a2l

sns.set(style='ticks')
colors = ['#838487', '#1b1c1c']
sns.set_palette(sns.color_palette(colors))


def get_betas(base_folder):

    # basic specs
    aggregated = {}
    aggregated['merger'] = []
    aggregated['own_price'] = []
    aggregated['se_own_price'] = []
    aggregated['own_price_OLS'] = []
    aggregated['se_own_price_OLS'] = []

    # loop through folders in "All"
    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        # go inside folders with step9 finished
        if os.path.exists(merger_folder + '/demand_results_month.txt'):

            read_file = pd.read_csv(merger_folder + "/demand_results_month.txt",
                                    sep="\t")
            read_file = read_file.replace(np.nan, '', regex=True)
            read_file.to_csv(merger_folder + "/demand_results_month.csv",
                             index=None)

            NL_merger = pd.read_csv(merger_folder + '/demand_results_month.csv',
                                    sep=',')
            NL_merger.index = NL_merger['Unnamed: 0']

            if '(2)' in NL_merger.columns:
                (aggregated['merger'].append(folder))
                (aggregated['own_price'].
                    append(NL_merger['(1)']['prices']))
                (aggregated['se_own_price'].
                    append(NL_merger['(1)'][(NL_merger.index.
                           get_loc('prices')+1)]))
                (aggregated['own_price_OLS'].
                    append(NL_merger['(2)']['prices']))
                (aggregated['se_own_price_OLS'].
                    append(NL_merger['(2)'][(NL_merger.index.
                           get_loc('prices')+1)]))

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    #df = aux.clean_betas(df)
    df.to_csv('NL_aggregated.csv', sep=',')


base_folder = '../../../All/'

log_out = open('output/NL_aggregation.log', 'w')
log_err = open('output/NL_aggregation.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

base_folder = '../../../All/'

get_betas(base_folder)

# basic_plot(spec)
# basic_plot2(spec)
