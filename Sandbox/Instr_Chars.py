import re
import os
import pandas as pd


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


def get_instr(folders, base_folder):

    progress = {}
    progress['merger'] = []

    for inst in range(15):
        progress['Inst_'+str(inst)] = []

    for folder in folders:

        merger_folder = base_folder + folder + '/'
        infotxt = merger_folder + 'info.txt'

        progress['merger'].append(folder)

        info = parse_info(infotxt)

        if 'Instruments' in info:

            Instruments = [i.lstrip() for i in info['Instruments'].split(',')]

            for inst in range(15):

                try:

                    progress['Inst_+'str(inst)].append(Instruments[inst])

                except IndexError:

                    progress['Inst_+'str(inst)].append('None')

    df = pd.DataFrame.from_dict(progress)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
    df.to_csv('Instr_Chars.csv', sep=',')


base_folder = '../../All/'

codes = (['m_1785984020_11', 'm_2664559020_1', 'm_2735179020_1',
          'm_2735179020_4', 'm_2736521020_10', 'm_2033113020_1_OLD',
          'm_2033113020_2', 'm_2675324040_1', 'm_2033113020_3',
          'm_2838188020_1', 'm_2033113020_3_OLD', 'm_2033113020_2_OLD',
          'm_m_2203820020_6', 'm_2813860020_1'])

folders = [folder for folder in os.listdir(base_folder) if folder not in codes]

log_out = open('output/Instr.log', 'w')
log_err = open('output/Instr.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

get_instr(folders, base_folder)
