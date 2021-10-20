import sys
import pandas as pd
import numpy as np
import unicodecsv as csv
import auxiliary as aux
import subprocess
import os
import re

def check_overlap(merger_folder):

	overlap_file = pd.read_csv(merger_folder + '/overlap.csv', sep=',')
	merging_sum = overlap_file['merging_party'].sum()

	if merging_sum < 2:
		return False

	elif merging_sum == 3:
		return True

	elif merging_sum == 2:

		df_merging = overlap_file[overlap_file['merging_party'] == 1]

		if (((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0))):
			return False

		else:
			return True


def parse_info(code):
	file = open('../../../All/m_' + code + '/info.txt', mode = 'r')
	info_file = file.read()
	file.close()

	all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
	info_dict = {}
	for info in all_info_elements:
		info_name = info.group(1).strip()
		info_content = info.group(2).strip()
		info_dict[info_name] = info_content
	return info_dict


def did_dma(folder, month_or_quarter='month'):

	code = folder[15:]
	base_folder = "../../../All/"
	merger_folder = base_folder + "m_" + code + "/output"
	path_input = base_folder + "m_" + code + "/intermediate"

	info_dict = parse_info(code)
	year_c = info_dict['DateCompleted'][0:4]
	month_c = str(int(info_dict['DateCompleted'][5:7]))
	year_a = info_dict['DateAnnounced'][0:4]
	month_a = str(int(info_dict['DateAnnounced'][5:7]))

		'''
		#open the did data
		df = pd.read_csv(path_input + "/stata_did_month.csv",
						 sep=",", index_col=['brand_code_uc', 'owner', 'dma_code', 'year', 'month'])

		# open demand data to get instruments
		inst = pd.read_csv(path_input + "/demand_month.csv",
						   delimiter=',', index_col=['upc', 'dma_code', 'year', 'month'])
		demand_cols = [col for col in inst if col.startswith('demand')]
		inst = inst[demand_cols]

		# open distance data
		dist = pd.read_csv(path_input + "/distances.csv",
						   delimiter=',', index_col=['brand_code_uc', 'owner', 'dma_code', 'year', 'month'])

		# merge did data with distances
		df = df.merge(dist, on=['brand_code_uc', 'owner', 'dma_code', 'year', 'month'],
					  how='left')

		# merge did data with instruments
		df = df.reset_index()
		df = df.set_index(['upc', 'dma_code', 'year', 'month'])
		df = pd.merge(df, inst, on=['upc', 'dma_code', 'year', 'month'],
					  how='left')

		df = df.reset_index()
		df.to_csv(path_input + '/stata_did_int_month.csv',
				  sep=',', encoding='utf-8', index=False)

		#print(folder)
		'''
	dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/DiD_interactions2.do"
	DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"

	codes = ['1817013020_1', '1924129020_11', '1923401020_1', '2614332020_1', '2736521020_9']

	if code not in codes:

		path_output = "../output/"
		cmd = ([DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input,
	            path_output, month_or_quarter, year_c, month_c, year_a, month_a])
		subprocess.call(cmd)


folder = sys.argv[1]
log_out = open('output/Did_all.log', 'a')
log_err = open('output/Did_all.err', 'a')
sys.stdout = log_out
sys.stderr = log_err
#print('before function: '+ folder)
#base_folder = '../../../All/'
#folders = [folder for folder in os.listdir(base_folder)]
#print(folder)
#for folder in folders:
#if os.path.exists(folder + '/intermediate/stata_did_month.csv'):
if os.path.exists(folder + '/intermediate/stata_did_int_month.csv'):
	print('for loop :' + folder)
	did_dma(folder)
#did_dma(folder)
