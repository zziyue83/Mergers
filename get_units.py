import re
import sys
from os import path
from datetime import datetime
import unicodecsv as csv

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

def load_store_table(year):
    store_path = "../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
    store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
    print("Loaded store file of "+ year)
    return store_table

def load_chunked_year_module_movement_table(year, group, module, path = ''):
    if path == '':
        movement_path = "../../Data/nielsen_extracts/RMS/" + year + "/Movement_Files/" + group + "_" + year + "/" + module + "_" + year + ".tsv"
        movement_table = pd.read_csv(movement_path, delimiter = "\t", chunksize = 10000000)
    else:
        movement_table = pd.read_csv(path, delimiter = "\t", chunksize = 10000000)
    return movement_table

def generate_units_table(code, years, groups, modules):

	with open('m_' + code + '/intermediate/units.csv', "wb") as csvfile:
		header = ["group", "module", "units", "count", "median", "mode"]
		writer = csv.writer(csvfile, delimiter = ',', encoding = 'utf-8')
		writer.writerow(header)


		for group, module in zip(groups, modules):
			for year in years:
				movement_table = load_chunked_year_module_movement_table(year, group, module)
				
				for data_chunk in tqdm(movementTable):
					# Do something to get the frequency table of units

			# Spit out the frequency table of units at the group, module level
			writer.writerow(ROW GOES HERE)

def aggregate_movement(code, years, groups, modules, share_cutoff):

	# NOTES: Need to read in the units_edited.csv file to edit units, and normalize them below
	#        Need to make sure this spits out just two files per merger, for month and quarter, rather than year by year
	#        Spit out things like brand descriptions separately
	#        Shares need to be computed and products filtered by share.

	for year in years:
		store_table = load_store_table(year)
        store_map = store_table.to_dict()
        dma_map = store_map['dma_code']
        area_month_upc_list = []

		for group, module in zip(groups, modules):
			movement_table = load_chunked_year_module_movement_table(year, group, module)

			for data_chunk in tqdm(movementTable):
                data_chunk['month'] = data_chunk['week_end']/100
                data_chunk['month'] = data_chunk['month'].astype(int)
                data_chunk['dma_code'] = data_chunk['store_code_uc'].map(dma_map)
                data_chunk['sales'] = data_chunk['price'] * data_chunk['units'] / data_chunk['prmult']
                area_month_upc = data_chunk.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
                area_month_upc_list.append(area_month_upc)

            area_month_upc = pd.concat(area_month_upc_list)
            area_month_upc = area_month_upc.groupby(['month', 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_month_upc.columns)
            area_month_upc['brand_code_uc'] = area_month_upc['upc'].map(productMap['brand_code_uc'])
            area_month_upc['brand_descr'] = area_month_upc['upc'].map(productMap['brand_descr'])
            area_month_upc['multi'] = area_month_upc['upc'].map(productMap['multi'])
            area_month_upc['size1_amount'] = area_month_upc['upc'].map(productMap['size1_amount'])
            area_month_upc['size1_units'] = area_month_upc['upc'].map(productMap['size1_units'])
            area_month_upc['volume'] = area_month_upc['units'] * area_month_upc['size1_amount'] * area_month_upc['multi']
            area_month_upc['raw_price']  = area_month_upc['price']
            area_month_upc['price'] = area_month_upc['sales'] / area_month_upc['volume']
            area_month_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)
            if firstFile:
                area_month_upc.to_csv(savePath, sep = '\t', encoding = 'utf-8')
                firstFile = False
            else:
                area_month_upc.to_csv(savePath, sep = '\t', encoding = 'utf-8', mode = 'a', header = False)
            print("Saved dma_month_upc data for year "+year+", group: "+group+", product: "+product+", file: "+file)
            print(area_month_upc.shape)

	


code = sys.argv[1]
info_dict = parse_info(code)

groups, modules = get_groups_and_modules(info_dict["MarketDefinition"])
years = get_years(info_dict["DateCompleted"])

#generate_units_table()


print(info_dict)
print(groups)
print(modules)
print(years)