
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
        if os.path.exists(merger_folder + '/NL_All_month.txt'):
            print(folder)


base_folder = '../../../All/'

log_out = open('output/NL_All_agg_count.log', 'w')
log_err = open('output/NL_All_agg_count.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

base_folder = '../../../All/'

get_betas(base_folder)

# basic_plot(spec)
# basic_plot2(spec)
