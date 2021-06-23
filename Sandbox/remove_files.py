import re
import os
import pandas as pd
import sys
import numpy as np

def remove_files(base_folder):

    folders = [folder for folder in os.listdir(base_folder)]

    for folder in folders:

        data_path = '../../../All/' + folder + '/intermediate/'

        print(data_path)

        if os.path.exists(data_path + 'stata_did_int_month.csv'):

            print(folder)

            if os.path.exists(data_path + 'stata_did_month.csv'):

                print('deleted')
                os.remove(data_path + 'stata_did_month.csv')


base_folder = '../../../All/'

log_out = open('output/remove_files.log', 'w')
log_err = open('output/remove_files.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

remove_files(base_folder)
