import re
import os
import pandas as pd
import sys
import numpy as np


def parse_info(file):

    file = open(file, mode='r')
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


def get_merger_to_fix(base_folder):

    # Codes with some type of fix in "clean_data.py"
    Codes = ['2600981020_1', '1973045020_1', '2614332020_1', '2736521020_1', '2735179020_11', '2735179020_20',
             '3035705020_5', '3035705020_7', '3035705020_8', '3035705020_10', '3035705020_13', '2820516020_1',
             '2972389020_26', '2972389020_8', '2495767020_10']

    Codes = ['m_' + code for code in Codes]

    Groups  = []
    Modules = []

    for code in Codes:

        infotxt = base_folder + code + '/info.txt'
        info = parse_info(infotxt)
        groups, modules = get_groups_and_modules(info["MarketDefinition"])

        Groups.extend(groups)
        Modules.extend(modules)

    folders = [folder for folder in os.listdir(base_folder) if folder not in Codes]

    aggregated = {}
    aggregated['merger'] = []
    aggregated['fix'] = []

    for folder in folders:

        infotxt = base_folder + folder + '/info.txt'

        if os.path.exists(infotxt):

            print(folder)

            info = parse_info(infotxt)
            groups, modules = get_groups_and_modules(info["MarketDefinition"])

            check =  any(item in modules for item in Modules)

            aggregated['merger'].append(folder)

            if check:
                aggregated['fix'].append(1)
            else:
                aggregated['fix'].append(0)

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df.to_csv('output/mergers_to_fix.csv', sep=',')


log_out = open('output/codes_to_fix.log', 'w')
log_err = open('output/codes_to_fix', 'w')
sys.stdout = log_out
sys.stderr = log_err

base_folder = '../../../All/'
get_merger_to_fix(base_folder)
