import re
import sys
from datetime import datetime
import auxiliary as aux
import tqdm
import numpy as np

def load_store_table(year):
    store_path = "../../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
    store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
    print("Loaded store file of "+ year)
    return store_table

def get_conversion_map(code, final_unit, method = 'mode'):
	# Get in the conversion map -- size1_units, multiplication
	master_conversion = pd.read_csv('master/unit_conversion.csv')
	master_conversion = master_conversion[master_conversion['final_unit'] == final_unit]

	these_units = pd.read_csv('../../../All/m_' + code + '/properties/units_edited.csv')
	these_units['conversion'] = 0

	# Anything that has convert = 1 must be in the master folder
	convertible = these_units.loc[these_units.convert == 1].copy()
	for this_unit in convertible.unit.unique():
		convert_factor = master_conversion.conversion[master_conversion.initial_unit == this_unit]
		these_units.loc[these_units.unit == this_unit, 'conversion'] = convert_factor
		convertible.loc[convertible.unit == this_unit, 'conversion'] = convert_factor

	# The "method" for convert = 0 is mapped to the "method" for the convert = 1
	# with the largest quantity
	where_largest = convertible.total_quantity.idxmax()
	if method == 'mode':
		base_size = convertible.mode[where_largest]
		other_size = these_units.mode[these_units.convert == 0]
	else:
		base_size = convertible.median[where_largest]
		other_size = these_units.median[these_units.convert == 0]

	these_units.conversion[these_units.convert == 0] = convertible.conversion[where_largest] * base_size / other_size
	these_units = these_units[['initial_size', 'conversion']]
	these_units = these_units.rename(columns = {'initial_size' : 'size1_units'})
	these_units = these_units.set_index('size1_units')

	conversion_map = these_units.to_dict()
	return conversion_map

def aggregate_movement(code, years, groups, modules, month_or_quarter, conversion_map, market_size_scale = 1.5):

	# NOTES: Need to read in the units_edited.csv file to edit units, and normalize them below
	#        Spit out things like brand descriptions separately
	#        Shares need to be computed and products filtered by share -- but maybe do this separately?

	area_time_upc_list = []
	product_map = aux.get_product_map(groups.unique())
	add_from_map = ['brand_code_uc', 'brand_descr', 'multi', 'size1_units', 'size1_amount']
	aggregation_function = {'week_end' : 'first', 'units' : 'sum', 'prmult' : 'mean', 'price' : 'mean', 'feature' : 'first', 'display' : 'first', 'store_code_uc' : 'first', 'sales' : 'sum'}

	for year in years:
		store_table = load_store_table(year)
        store_map = store_table.to_dict()
        dma_map = store_map['dma_code']

		for group, module in zip(groups, modules):
			movement_table = aux.load_chunked_year_module_movement_table(year, group, module)

			for data_chunk in tqdm(movement_table):
				data_chunk['year'] = np.floor(data_chunk['week_end']/10000)
				data_chunk['year'] = data_chunk['year'].astype(int)
				if month_or_quarter == "month":
					data_chunk[month_or_quarter] = np.floor((data_chunk['week_end'] % 10000)/100)
					data_chunk[month_or_quarter] = data_chunk[month_or_quarter].astype(int)
            	elif month_or_quarter == "quarter":
					data_chunk[month_or_quarter] = np.ceil(np.floor((data_chunk['week_end'] % 10000)/100)/3)
					data_chunk[month_or_quarter] = data_chunk[month_or_quarter].astype(int)

                data_chunk['dma_code'] = data_chunk['store_code_uc'].map(dma_map)
                data_chunk['sales'] = data_chunk['price'] * data_chunk['units'] / data_chunk['prmult']
                area_time_upc = data_chunk.groupby(['year', month_or_quarter, 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
                area_time_upc_list.append(area_time_upc)

    area_time_upc = pd.concat(area_time_upc_list)
    area_time_upc = area_time_upc.groupby(['year', month_or_quarter, 'upc','dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_time_upc.columns)
    for to_add in add_from_map:
    	area_time_upc[to_add] = area_time_upc['upc'].map(product_map(to_add))
    area_time_upc['conversion'] = area_time_upc['size1_units'].map(conversion_map['conversion']) # YINTIAN/AISLING -- check this!!!
    area_time_upc['volume'] = area_time_upc['units'] * area_time_upc['size1_amount'] * area_time_upc['multi'] * area_time_upc['conversion']
    area_time_upc['raw_price']  = area_time_upc['price']
    area_time_upc['prices'] = area_time_upc['sales'] / area_time_upc['volume']
    area_time_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)

    # Normalize the prices by the CPI.  Let January 2010 = 1.
    area_time_upc = aux.adjust_inflation(area_time_upc, 'prices', month_or_quarter)

    # Get the market sizes here, by summing volume within dma-time and then taking 1.5 times max within-dma
    short_area_time_upc = area_time_upc[['dma_code', 'year', month_or_quarter, 'volume']]
    market_sizes = area_time_upc.groupby(['dma_code', 'year', month_or_quarter]).sum()
    market_sizes = market_sizes.rename({'volume : market_size'})
    market_sizes['market_size'] = market_size_scale * market_sizes['market_size']
    market_sizes.to_csv('../../../All/m_' + code + '/intermediate/market_sizes.csv', sep = ',', encoding = 'utf-8')

    # Shares = volume / market size.  Map market sizes back and get shares.
    area_time_upc = area_time_upc.join(market_sizes, on = ['dma_code', 'year', month_or_quarter])
    area_time_upc['shares'] = area_time_upc['volume'] / area_time_upc['market_size']

    return area_time_upc

def get_acceptable_upcs(area_month_upc, share_cutoff):
    # Now for each UPC, find the max market share across all DMA-month.  If it's less than the share cutoff, then drop that upc
    upc_max_share = area_month_upc.groupby('upc').max()
    acceptable_upcs = upc_max_share[upc_max_share['shares'] > share_cutoff]

    return acceptable_upcs['upc']

def write_brands_upc(code, agg, upc_set):
	agg = agg[['upc', 'upc_descr', 'brand_code_uc', 'brand_descr', 'size1_units', 'size1_amount', 'multi']]
	agg = agg.drop_duplicates()
	agg = agg[agg.upc.isin(upc_set)]
	agg = agg.sort_values(by = 'brand_descr')

	base_folder = '../../../All/m_' + code + '/intermediate/'
	agg.to_csv(base_folder + 'upcs.csv', sep = ',', encoding = 'utf-8')

	agg = agg[['brand_code_uc', 'brand_descr']]
	agg = agg.rename(columns = {'brand_descr' : 'brand'})
	agg = agg.drop_duplicates()
	agg.to_csv(base_folder + 'brands.csv', sep = ',', encoding = 'utf-8')

def write_base_dataset(code, agg, upc_set, month_or_quarter = 'month'):
	agg = agg[['upc', 'dma_code', 'year', month_or_quarter, 'prices', 'shares']]
	agg = agg[agg.upc.isin(upc_set)]
	agg.to_csv('../../../All/m_' + code + '/intermediate/data_' + month_or_quarter + '.csv', sep = ',', encoding = 'utf-8')

def write_market_coverage(code, agg, upc_set):
	agg = agg[['upc', 'dma_code', 'year', month_or_quarter, 'shares']]
	agg = agg[agg.upc.isin(upc_set)]
	agg = agg[['dma_code', month_or_quarter, 'shares']]

	agg = agg.groupby(['dma_code', 'year', month_or_quarter]).sum()
	agg = agg.rename(columns = {'shares' : 'total_shares'})
	agg.to_csv('../../../All/m_' + code + '/intermediate/market_coverage.csv', sep = ',', encoding = 'utf-8')

	print("Summary Statistics for Total Shares")
	agg.total_shares.describe(percentiles = [0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99])

code = sys.argv[1]
log_out = open('../../../All/m_' + code + '/output/select_products.log', 'w')
log_err = open('../../../All/m_' + code + '/output/select_products.err', 'w')
sys.stdout = log_out
sys.stderr = log_err


info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateCompleted"])

conversion_map = get_conversion_map(code, info_dict["FinalUnit"])
area_month_upc = aggregate_movement(code, years, groups, modules, "month", conversion_map)
area_quarter_upc = aggregate_movement(code, years, groups, modules, "quarter", conversion_map)

acceptable_upcs = get_acceptable_upcs(area_month_upc['upc', 'shares'], float(info_dict["InitialShareCutoff"]))

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



# Close the logs
log_out.close()
log_err.close()