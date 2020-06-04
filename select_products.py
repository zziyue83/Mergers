import re
import sys
from datetime import datetime
import auxiliary as aux
import tqdm

def load_store_table(year):
    store_path = "../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
    store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
    print("Loaded store file of "+ year)
    return store_table

def get_conversion_map(code, final_unit, method = 'mode'):
	# Get in the conversion map -- size1_units, multiplication
	master_conversion = pd.read_csv('master/unit_conversion.csv')
	master_conversion = master_conversion[master_conversion['final_unit'] == final_unit]

	these_units = pd.read_csv('m_' + code + '/properties/units_edited.csv')
	these_units['conversion'] = 0

	# Anything that has convert = 1 must be in the master folder
	convertible = these_units.unit[these_units.convert == 1]
	for this_unit in convertible.unique():
		convert_factor master_conversion.conversion[master_conversion.initial_unit == this_unit]
		these_units.conversion[these_units.unit == this_unit] = convert_factor

	# How does the convert == 0 work???

	conversion_map = conversions.to_dict()
	return conversion_map

def aggregate_movement(code, years, groups, modules, month_or_quarter, conversion_map):

	# NOTES: Need to read in the units_edited.csv file to edit units, and normalize them below
	#        Spit out things like brand descriptions separately
	#        Shares need to be computed and products filtered by share -- but maybe do this separately?

	area_time_upc_list = []

	for year in years:
		store_table = load_store_table(year)
        store_map = store_table.to_dict()
        dma_map = store_map['dma_code']
        
		for group, module in zip(groups, modules):
			movement_table = aux.load_chunked_year_module_movement_table(year, group, module)

			# Add in year somehwere?

			for data_chunk in tqdm(movement_table):
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
        area_time_upc['prices'] = area_time_upc['sales'] / area_time_upc['volume']
        area_time_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)
        # Get shares???
        # Normalize by units???

    return area_time_upc

def get_acceptable_upcs(area_month_upc, share_cutoff):
    # Now for each UPC, find the max market share across all DMA-month.  If it's less than the share cutoff, then drop that upc
    upc_max_share = area_month_upc.groupby('upc').max()
    acceptable_upcs = upc_max_share[upc_max_share['shares'] > share_cutoff]

    return acceptable_upcs['upc']

def write_brands_upc(code, agg, upc_set):
	agg = agg[['upc', 'upc_descr', 'brand_code_uc', 'brand_descr']]
	agg = agg.drop_duplicates
	agg = agg[agg.upc.isin(upc_set)]

	base_folder = 'm_' + code + '/intermediate/'
	agg.to_csv(base_folder + 'upcs.csv', sep = ',', encoding = 'utf-8')

	agg = agg[['brand_descr']]
	agg = agg.rename(columns = {'brand_descr' : 'brand'})
	agg = agg.drop_duplicates
	agg.to_csv(base_folder + 'brands.csv', sep = ',', encoding = 'utf-8')	

def write_base_dataset(code, agg, upc_set, month_or_quarter = 'month'):
	agg = agg[['upc', 'dma_code', 'year', month_or_quarter, 'prices', 'shares']]
	agg = agg[agg.upc.isin(upc_set)]
	agg.to_csv('m_' + code + '/intermediate/data_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8')

def write_market_coverage(code, agg, upc_set):
	agg = agg[['upc', 'dma_code', 'year', month_or_quarter, 'shares']]
	agg = agg[agg.upc.isin(upc_set)]
	agg = agg[['dma_code', 'year', month_or_quarter, 'shares']]

	agg = agg.groupby(['dma_code', 'year', month_or_quarter]).sum()
	agg = agg.rename(columns = {'shares' : 'total_shares'})
	agg.to_csv('m_' + code + '/intermediate/market_coverage.csv', sep = ',', encoding = 'utf-8')

#Example:
# upc                                   15000004
# upc_ver_uc                                   1
# upc_descr               SIERRA NEVADA W BR NRB
# product_module_code                       5000
# product_module_descr                      BEER
# product_group_code                        5001
# product_group_descr                       BEER
# department_code                              8
# department_descr           ALCOHOLIC BEVERAGES
# brand_code_uc                           637860
# brand_descr                SIERRA NEVADA WHEAT
# multi                                        1
# size1_code_uc                            32992
# size1_amount                                12
# size1_units                                 OZ
# dataset_found_uc                           ALL
# size1_change_flag_uc                         0

code = sys.argv[1]
info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateCompleted"])

conversion_map = get_conversion_map(code, info_dict["FinalUnit"])
area_month_upc = aggregate_movement(code, years, groups, modules, "month", conversion_map)
area_quarter_upc = aggregate_movement(code, years, groups, modules, "quarter", conversion_map)

acceptable_upcs = get_acceptable_upcs(area_month_upc['upc', 'shares'], info_dict["InitialShareCutoff"])

# Find the unique brands associated with the acceptable_upcs and spit that out into brands.csv
# Get the UPC information you have for acceptable_upcs and spit that out into upc_dictionary.csv
write_brands_upc(code, area_month_upc, acceptable_upcs)

# Now filter area_month_upc and area_quarter_upc so that only acceptable_upcs survive
# Print out data_month.csv and data_quarter.csv
write_base_dataset(code, area_month_upc, acceptable_upcs, 'month')
write_base_dataset(code, area_quarter_upc, acceptable_upcs, 'quarter')

# Aggregate data_month (sum shares) by dma-month to get total market shares and spit that out as market_coverage.csv
write_market_coverage(code, area_month_upc, acceptable_upcs)

# How do you do Nielsen Characteristics excel file?


