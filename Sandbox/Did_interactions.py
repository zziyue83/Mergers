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
        path_input = "../../../All/" + folder + "/intermediate"

        if (os.path.exists(path_input + '/demand_month.csv')) and check_overlap(merger_folder):

            code = folder[2:]
            info_dict = aux.parse_info(code)
            year_c = info_dict['DateCompleted'][0:4]
            month_c = str(int(info_dict['DateCompleted'][5:7]))
            year_a = info_dict['DateAnnounced'][0:4]
            month_a = str(int(info_dict['DateAnnounced'][5:7]))

            print(code)
            # open the data, and get distances
            df = pd.read_csv(path_input + "/stata_did_month.csv",
                             sep=",", index_col=['brand_code_uc', 'dma_code', 'owner'])
            inst = pd.read_csv(path_input + "/demand_month.csv",
                               delimiter=',', index_col=['upc', 'dma_code', 'year', 'month'])
            dist = pd.read_csv(path_input + "/distances.csv",
                               delimiter=',', index_col=['brand_code_uc', 'dma_code', 'owner'])

            df = df.merge(dist, on=['brand_code_uc', 'dma_code'],
                          how='left')

            df = df.reset_index()
            try:
                df = df.set_index(['upc', 'dma_code', 'year', 'month'])
            except KeyError:
                df = df.rename(columns={'year_x': 'year', 'month_x': 'month'})
                df = df.set_index(['upc', 'dma_code', 'year', 'month'])

            # recover instrument columns
            demand_cols = [col for col in inst if col.startswith('demand')]
            inst = inst[demand_cols]
            df = pd.merge(df, inst, on=['upc', 'dma_code', 'year', 'month'],
                          how='left')

            df = df.reset_index()
            df.to_csv(path_input + '/stata_did_int_month.csv',
                      sep=',', encoding='utf-8', index=False)

            print(folder)
            dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/DiD_interactions2.do"
            DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
            path_output = "../output/"
            cmd = ([DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input,
                    path_output, month_or_quarter, year_c, month_c, year_a, month_a])
            subprocess.call(cmd)


log_out = open('output/did_int.log', 'w')
log_err = open('output/did_int.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'
did_dma(base_folder)