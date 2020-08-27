import re
import os
import pandas as pd

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

def check_overlap(merger_folder):

	if os.path.exists(merger_folder+'output/overlap.csv'):

		overlap_file = pd.read_csv(merger_folder + 'output/overlap.csv', sep=',')
		merging_sum = overlap_file['merging_party'].sum()

		if merging_sum < 2:
			return False

		elif merging_sum ==3:
			return True

		elif merging_sum == 2:

			df_merging = overlap_file[overlap_file['merging_party'] == 1]

			if ((df_merging.loc[0,'pre_share'] == 0) & (df_merging.loc[1,'post_share'] == 0)) | ((df_merging.loc[0,'post_share'] == 0) & (df_merging.loc[1,'pre_share'] == 0)):
				return False

			else:

				return True

	else:

		return False

def track_progress(base_folder):
	progress = {}
	progress['RA'] = []
	progress['merger'] = []
	for step in range(1,11):
		progress['step'+str(step)] = []
	for folder in os.listdir(base_folder):
		if len(folder) > 10 and folder[0] == 'm':
			progress['merger'].append(folder)
			progress['RA'].append('info.txt does not exist')
			for step in range(1,11):
				progress['step'+str(step)].append('incomplete')
			merger_folder = base_folder + folder + '/'
			infotxt = merger_folder + 'info.txt'
			if os.path.exists(infotxt):
				info = parse_info(merger_folder + 'info.txt')
				progress['RA'][-1] = info.get('ResearchAssistant', 'not entered')
				progress['step1'][-1] = 'complete'
			else:
				continue
			if os.path.exists(merger_folder+'properties/units_edited.csv'):
				progress['step2'][-1] = 'complete'
			if os.path.exists(merger_folder+'intermediate/market_coverage.csv'):
				progress['step3'][-1] = 'complete'
			if os.path.exists(merger_folder+'properties/ownership.csv'):
				progress['step4'][-1] = 'complete'
			if os.path.exists(merger_folder+'output/did_stata_month_0.csv') & check_overlap(merger_folder):
				progress['step5'][-1] = 'complete'
			if os.path.exists(merger_folder+'output/did_stata_month_0.csv') & (not (check_overlap(merger_folder))):
				progress['step5'][-1] = 'no_overlap'
			if os.path.exists(merger_folder+'output/did_month.csv') & (not os.path.exists(merger_folder+'output/did_stata_month_0.csv')):
				progress['step5'][-1] = 'update'
			if os.path.exists(merger_folder+'properties/characteristics.csv'):
				progress['step6'][-1] = 'complete'
			if os.path.exists(merger_folder+'intermediate/distances.csv'):
				progress['step7'][-1] = 'complete'
			if 'Instruments' in info:
				progress['step8'][-1] = 'complete'
			if os.path.exists(merger_folder+'Nested_Logit.pdf'):
				progress['step9'][-1] = 'complete'

	df = pd.DataFrame.from_dict(progress)
	df = df.sort_values(by = 'RA').reset_index().drop('index', axis=1)
	df.to_csv('progress.csv', sep = ',')

base_folder = '../../All/'
track_progress(base_folder)



