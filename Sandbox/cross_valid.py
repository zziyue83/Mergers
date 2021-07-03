import subprocess
import os
import re
import sys
import pandas as pd
import unicodecsv as csv
import auxiliary as aux


def CV(folder, month_or_quarter='month'):

        merger_folder = folder + '/output'

        print('Calling Stata: ' + folder)
        code = folder[15:]
        info_dict = aux.parse_info(code)
        year = info_dict['DateCompleted'][0:4]
        month = str(int(info_dict['DateCompleted'][5:7]))

        if not os.path.isdir(folder + '/output/tables'):
            os.makedirs(folder + '/output/tables')

        dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/cross_valid.do"
        DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
        path_input = folder + "/intermediate"
        path_output = "../output"
        cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, year, month]
        subprocess.call(cmd)


folder = sys.argv[1]
log_out = open('output/CV_All.log', 'a')
log_err = open('output/CV_All.err', 'a')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'

print(folder)

if os.path.exists(folder + '/output/demand_results_month.txt'):
    CV(folder)
