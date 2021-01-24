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


def did_dma(folder, month_or_quarter='month'):

    merger_folder = folder + '/output'
    path_input = folder + "/intermediate"

    if (os.path.exists(path_input + '/stata_did_int_month.csv')):

        code = folder[15:]
        info_dict = aux.parse_info(code)
        year_c = info_dict['DateCompleted'][0:4]
        month_c = str(int(info_dict['DateCompleted'][5:7]))
        year_a = info_dict['DateAnnounced'][0:4]
        month_a = str(int(info_dict['DateAnnounced'][5:7]))

        print(code)

        dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/DiD_interactions2.do"
        DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
        path_output = "../output/"
        cmd = ([DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input,
               path_output, month_or_quarter, year_c, month_c, year_a, month_a])
        subprocess.call(cmd)


folder = sys.argv[1]
log_out = open('output/did_parallel.log', 'a')
log_err = open('output/did_parallel.err', 'a')
sys.stdout = log_out
sys.stderr = log_err
did_dma(folder)
