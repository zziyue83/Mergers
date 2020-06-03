import re
import sys
from datetime import datetime
import auxiliary as aux

def load_store_table(year):
    store_path = "../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
    store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
    print("Loaded store file of "+ year)
    return store_table

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
			movement_table = aux.load_chunked_year_module_movement_table(year, group, module)

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
    upc_max_share = area_month_upc.groupby('upc').max()
    acceptable_upcs = upc_max_share[upc_max_share['shares'] > share_cutoff]

    return acceptable_upcs['upc']



code = sys.argv[1]
info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateCompleted"])

area_month_upc = aggregate_movement(code, years, groups, modules, "month")
area_quarter_upc = aggregate_movement(code, years, groups, modules, "quarter")

acceptable_upcs = find_acceptable_upcs(area_month_upc['upc', 'shares'], info_dict["InitialShareCutoff"])

# Find the unique brands associated with the acceptable_upcs and spit that out into brands.csv
# Get the UPC information you have for acceptable_upcs and spit that out into upc_dictionary.csv
# Now filter area_month_upc and area_quarter_upc so that only acceptable_upcs survive
# Print out data_month.csv and data_quarter.csv
# Aggregate data_month (sum shares) by dma-month to get total market shares and spit that out as market_coverage.csv
# How do you do Nielsen Characteristics excel file?


