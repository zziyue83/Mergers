import re
import sys
from datetime import datetime

def parse_info(code):
	file = open('m_' + code + '/info.txt', mode = 'r')
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

def get_years(year_string, pre = 2, post = 2):
	dt = datetime.strptime(year_string, '%Y-%m-%d')
	years = []
	for i in range(-pre, post + 1, 1):
		this_year = dt.year + i 
		if this_year >= 2006 and this_year <= 2017:
			years.append(str(this_year))
	return years

def load_chunked_year_module_movement_table(year, group, module, path = ''):
    if path == '':
        path = "../../Data/nielsen_extracts/RMS/" + year + "/Movement_Files/" + group + "_" + year + "/" + module + "_" + year + ".tsv"
    table = pd.read_csv(path, delimiter = "\t", chunksize = 10000000)
    return table
