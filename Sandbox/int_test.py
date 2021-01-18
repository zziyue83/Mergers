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

folder = 'm_1912896020_1'
path_input = "../../../All/" + folder + "/intermediate"

# open the data, and get distances
df = pd.read_csv(path_input + "/stata_did_month.csv",
                 sep=",", index_col=['upc', 'dma_code', 'year', 'month'])
inst = pd.read_csv(path_input + "/demand_month.csv",
                   delimiter=',', index_col=['upc', 'dma_code', 'year', 'month'])
dist = pd.read_csv(path_input + "/distances.csv",
                   delimiter=',', index_col=['brand_code_uc', 'owner', 'dma_code'])
df = df.join(dist, on=['brand_code_uc', 'owner', 'dma_code'],
             how='left')

# recover instrument columns
demand_cols = [col for col in inst if col.startswith('demand')]
inst = inst[demand_cols]
df = df.reset_index()
inst = inst.reset_index()
df2 = pd.merge(df, inst, on=['upc', 'dma_code', 'year', 'month'],
               how='left')

df2.to_csv(path_input + '/stata_did_int_month.csv',
           sep=',', encoding='utf-8', index=False)

log_out = open('output/did_int.log', 'w')
log_err = open('output/did_int.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
