import subprocess
import os
import re
import sys
import pandas as pd
import unicodecsv as csv
import auxiliary as aux
from datetime import datetime


def CV(base_folder, month_or_quarter='month'):

    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        if os.path.exists(merger_folder + '/demand_results_month.txt'):

            print(folder)
            code = folder[2:]
            info_dict = aux.parse_info(code)
            year = info_dict['DateCompleted'][0:4]
            month = str(int(info_dict['DateCompleted'][5:7]))
            if not os.path.isdir('../../../All/m_' + code + '/output/tables'):
				os.makedirs('../../../All/m_' + code + '/output/tables')

            dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/cross_valid.do"
            DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
            path_input = "../../../All/m_" + code + "/intermediate"
            path_output = "../output"
            cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, year, month]
            subprocess.call(cmd)


log_out = open('output/CV_All.log', 'w')
log_err = open('output/CV_All.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'
CV(base_folder)
