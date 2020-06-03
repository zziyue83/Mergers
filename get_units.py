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

def aggregate_movement(code, years, groups, modules, month_or_quarter):

	# NOTES: Need to read in the units_edited.csv file to edit units, and normalize them below
	#        Spit out things like brand descriptions separately
	#        Shares need to be computed and products filtered by share -- but maybe do this separately?

	area_time_upc_list = []

	for year in years:
		store_table = load_store_table(year)
        store_map = store_table.to_dict()
        dma_map = store_map['dma_code']
        
		for group, module in zip(groups, modules):
			movement_table = load_chunked_year_module_movement_table(year, group, module)

			# Add in year somehwere?

			for data_chunk in tqdm(movementTable):
				if month_or_quarter == "month":
                	data_chunk[month_or_quarter] = data_chunk['week_end']/100
                	data_chunk[month_or_quarter] = data_chunk['time'].astype(int)
                elif month_or_quarter == "quarter":
                	# Make time = quarter now
                data_chunk['dma_code'] = data_chunk['store_code_uc'].map(dma_map)
                data_chunk['sales'] = data_chunk['price'] * data_chunk['units'] / data_chunk['prmult']
                area_time_upc = data_chunk.groupby([month_or_quarter, 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
                area_time_upc_list.append(area_time_upc)

        area_time_upc = pd.concat(area_time_upc_list)
        area_time_upc = area_time_upc.groupby([month_or_quarter, 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_time_upc.columns)
        area_time_upc['brand_code_uc'] = area_time_upc['upc'].map(productMap['brand_code_uc'])
        area_time_upc['brand_descr'] = area_time_upc['upc'].map(productMap['brand_descr'])
        area_time_upc['multi'] = area_time_upc['upc'].map(productMap['multi'])
        area_time_upc['size1_amount'] = area_time_upc['upc'].map(productMap['size1_amount'])
        area_time_upc['size1_units'] = area_time_upc['upc'].map(productMap['size1_units'])
        area_time_upc['volume'] = area_time_upc['units'] * area_time_upc['size1_amount'] * area_time_upc['multi']
        area_time_upc['raw_price']  = area_time_upc['price']
        area_time_upc['price'] = area_time_upc['sales'] / area_time_upc['volume']
        area_time_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)
        # Get shares???
        # Normalize by units???

    return area_time_upc

def find_acceptable_upcs(area_month_upc, share_cutoff):
	
    # Now for each UPC, find the max market share across all DMA-month.  If it's less than the share cutoff, then drop that upc
    upc = area_month_upc.groupby('upc') # and find max?

    return acceptable_upcs



code = sys.argv[1]
what_to_do = sys.argv[2]
info_dict = parse_info(code)

groups, modules = get_groups_and_modules(info_dict["MarketDefinition"])
years = get_years(info_dict["DateCompleted"])

if what_to_do == "units":
	generate_units_table()
elif what_to_do == "select":
	area_month_upc = aggregate_movement(code, years, groups, modules, "month")
	area_quarter_upc = aggregate_movement(code, years, groups, modules, "quarter")
	
	acceptable_upcs = find_acceptable_upcs(area_month_upc, info_dict["InitialShareCutoff"])
	# Now print out the stuff that's acceptable UPCs to generate the data_month and data_quarter files





print(info_dict)
print(groups)
print(modules)
print(years)