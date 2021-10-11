import re
import sys
from datetime import datetime
import pyblp
import pickle
import pandas as pd
import numpy as np
import pandasql as ps
import os
import tqdm

def int_to_month(value):
    year = np.floor((value - 1) / 12)
    month = value - 12 * year
    return year, month


def parse_info(file):
    file = open(file, mode = 'r')
    info_file = file.read()
    file.close()

    all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
    info_dict = {}
    for info in all_info_elements:
        info_name = info.group(1).strip()
        info_content = info.group(2).strip()
        info_dict[info_name] = info_content
    return info_dict


def get_groups_and_modules(full_string):
    all_group_module = re.finditer('{(.*?),(.*?)}', full_string, re.DOTALL)
    groups = []
    modules = []
    for pair in all_group_module:
        groups.append(pair.group(1).strip())
        modules.append(pair.group(2).strip())
    return groups, modules

def get_years(initial_year_string, final_year_string, pre_months = 24, post_months = 24):
    initial_dt = datetime.strptime(initial_year_string, '%Y-%m-%d')
    final_dt = datetime.strptime(final_year_string, '%Y-%m-%d')
    initial_month_int = initial_dt.year * 12 + initial_dt.month
    final_month_int = final_dt.year * 12 + final_dt.month
    min_year, min_month = int_to_month(initial_month_int - pre_months)
    max_year, max_month = int_to_month(final_month_int + post_months)

    years = []
    for i in range(int(min_year), int(max_year) + 1, 1):
        this_year = i
        if this_year >= 2006 and this_year <= 2018:
            years.append(str(this_year))
    return years


def get_merger_to_fix(base_folder):

    folders = [folder for folder in os.listdir(base_folder)]

    aggregated = {}
    aggregated['merger'] = []

    for i in range(12):
        aggregated['module'+str(i)] = []
        aggregated['group'+str(i)] = []

    for folder in folders:

        infotxt = base_folder + folder + '/info.txt'

        if os.path.exists(infotxt):

            print(folder)

            info = parse_info(infotxt)
            groups, modules = get_groups_and_modules(info["MarketDefinition"])
            years = get_years(info["DateAnnounced"], info["DateCompleted"])

            check =  '2017' in years

            if check:

                aggregated['merger'].append(folder)

                for i in range(12):
                    try:
                        aggregated['module'+str(i)].append(modules[i])
                        aggregated['group'+str(i)].append(groups[i])
                    except IndexError:
                        aggregated['module'+str(i)].append(np.nan)
                        aggregated['group'+str(i)].append(np.nan)

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df.to_csv('output/modules_to_download.csv', sep=',')


log_out = open('output/modules_to_download.log', 'w')
log_err = open('output/modules_to_download', 'w')
sys.stdout = log_out
sys.stderr = log_err

base_folder = '../../../All/'
get_merger_to_fix(base_folder)


