import re
import os
import pandas as pd
import sys
import numpy as np

def get_stats(base_folder):

    folders = [folder for folder in os.listdir(base_folder)]

    for folder in folders:

        data_path = '../../../All/' + folder + '/properties/'

        print(data_path)

        if os.path.exists(data_path + 'ownership.csv'):

            print(folder)

            df = pd.read_csv(data_path + 'ownership.csv', sep=',')
            ctl_br = df.loc[df['brand_code_uc'] == 536746]

            if not ctl_br.empty:
            	if 'owner' in ctl_br.columns:
            		print(ctl_br['owner'])


base_folder = '../../../All/'

log_out = open('output/ctl_br.log', 'w')
log_err = open('output/ctl_br.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

get_stats(base_folder)
