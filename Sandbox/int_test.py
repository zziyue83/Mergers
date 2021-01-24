import sys
import os

def fx(folder):

    merger_folder = folder + '/output'
    path_input = folder + "/intermediate"

    if os.path.exists(path_input + "/stata_did_int_month.csv"):
        print(folder)


log_out = open('output/count.log', 'a')
log_err = open('output/count.err', 'a')
sys.stdout = log_out
sys.stderr = log_err

folder = sys.argv[1]
fx(folder)
