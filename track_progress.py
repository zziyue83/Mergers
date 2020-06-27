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
			if os.path.exists(merger_folder+'output/did_month.csv'):
				progress['step5'][-1] = 'complete'
			if os.path.exists(merger_folder+'properties/characteristics.csv'):
				progress['step6'][-1] = 'complete'
			if os.path.exists(merger_folder+'intermediate/distances.csv'):
				progress['step7'][-1] = 'complete'
			if 'Instruments' in infotxt:
				progress['step8'][-1] = 'complete'
			if os.path.exists(merger_folder+'output/first_stage.csv'):
				progress['step9'][-1] = 'complete'

	df = pd.DataFrame.from_dict(progress)
	df = df.sort_values(by = 'RA')
	df.to_csv('progress.csv', sep = ',')

base_folder = '../../All/'
track_progress(base_folder)