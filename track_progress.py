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
			progress['RA'].append('not entered')
			for step in range(1,11):
				progress['step'+str(step)].append('incomplete')
			merger_folder = base_folder + folder + '/'
			infotxt = merger_folder + 'info.txt'
			if os.path.exists(infotxt):
				info = parse_info(merger_folder + 'info.txt')
				ra = info['ResearchAssistant']
				progress['RA'][-1] = ra
			else:
				continue
	df = pd.from_dict(progress)
	df.to_csv('progress.csv', sep = ',')

base_folder = '../../All/'
track_progress(base_folder)