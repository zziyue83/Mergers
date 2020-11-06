
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

    list = ["m_1817013020_1", "m_1973045020_1", "m_2203820020_9", "m_1817013020_3", "m_1923401020_1", "m_2143743020_1"]

    # basic specs
    aggregated = {}
    aggregated['merger'] = []
    for i in range(9):
        j = i+1
        aggregated['price_'+str(j)] = []
        aggregated['se_price_'+str(j)] = []
        aggregated['nest_'+str(j)] = []
        aggregated['se_nest_'+str(j)] = []

    # loop through folders in "All"
    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        # go inside folders with step9 finished
        if os.path.exists(merger_folder + '/NL_All_month.txt') & (folder not in list):
            print(folder)

            aggregated['merger'].append(folder)
            read_file = pd.read_csv(merger_folder + "/NL_All_month.txt",
                                    sep="\t")
            read_file = read_file.replace(np.nan, '', regex=True)
            read_file.to_csv(merger_folder + "/NL_All_month.csv",
                             index=None)

            NL_merger = pd.read_csv(merger_folder + '/NL_All_month.csv',
                                    sep=',')
            NL_merger.index = NL_merger['Unnamed: 0']

            for i in NL_merger.columns[1:]:
                j=i.rstrip(')').lstrip('(')
                aggregated['price_'+j].append(NL_merger[i]['prices'])
                aggregated['se_price_'+j].append(NL_merger[i][(NL_merger.index.get_loc('prices')+1)])

                aggregated['nest_'+j].append(NL_merger[i]['lwns'])
                aggregated['se_nest_'+j].append(NL_merger[i][(NL_merger.index.get_loc('lwns')+1)])

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    #df = aux.clean_betas(df)
    df.to_csv('NL_All_agg.csv', sep=',')


base_folder = '../../../All/'

log_out = open('output/NL_All_agg.log', 'w')
log_err = open('output/NL_All_agg.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

base_folder = '../../../All/'

get_betas(base_folder)

# basic_plot(spec)
# basic_plot2(spec)
