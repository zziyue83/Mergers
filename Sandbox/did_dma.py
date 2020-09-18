import sys
import pandas as pd
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import numpy as np
import unicodecsv as csv
import auxiliary as aux
from datetime import datetime
from linearmodels.panel import compare
import subprocess
import os

def check_overlap(merger_folder):

    overlap_file = pd.read_csv(merger_folder + '/overlap.csv', sep=',')
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


def did_dma(base_folder, month_or_quarter='month'):

    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        if (os.path.exists(merger_folder + '/did_stata_month_2.csv')) and check_overlap(merger_folder):

            print(folder)
            dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/did_dma.do"
            DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
            path_input = "../../../All/" + folder + "/intermediate"
            path_output = "../output/"
            cmd = ([DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input,
                    path_output, month_or_quarter, folder])
            subprocess.call(cmd)


log_out = open('output/did_dma.log', 'w')
log_err = open('output/did_dma.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'
did_dma(base_folder)
