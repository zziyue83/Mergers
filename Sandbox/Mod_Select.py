import subprocess
import os
import re
import sys
import pandas as pd
import unicodecsv as csv
import auxiliary as aux
from datetime import datetime


def Count(base_folder):

    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        if os.path.exists(merger_folder + '/tables'):
             if (len(os.listdir(merger_folder + '/tables')) != 0):

                print(folder)

log_out = open('output/Count.log', 'w')
log_err = open('output/Count.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'
Count(base_folder)
