import pandas as pd
import sys
import csv
from datetime import datetime, timedelta
from collections import OrderedDict
import numpy as np
import time

# check if I need to organize directory/path for auxiliary function imports
import auxiliary as aux

# using test case code
code = '2823116020_9'

## testing info
#df_pre = 
#month_or_quarter

# using parse_info to check information
def parse_info(code):
	file = open('../../../../All/m_' + code + '/info.txt', mode = 'r')
	info_file = file.read()
	file.close()

	all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
	info_dict = {}
	for info in all_info_elements:
		info_name = info.group(1).strip()
		info_content = info.group(2).strip()
		info_dict[info_name] = info_content
	return info_dict

def int_to_month(value):
    year = np.floor((value - 1) / 12)
    month = value - 12 * year
    return year, month

# function that creates same date range as found in data_months, need to give DateAnnounced and DateCompleted

def get_date_range(initial_year_string, final_year_string, pre_months = 24, post_months = 24):
    initial_dt = datetime.strptime(initial_year_string, '%Y-%m-%d')
    final_dt = datetime.strptime(final_year_string, '%Y-%m-%d')
    initial_month_int = initial_dt.year * 12 + initial_dt.month
    final_month_int = final_dt.year * 12 + final_dt.month
    min_year, min_month = int_to_month(initial_month_int - pre_months)
    max_year, max_month = int_to_month(final_month_int + post_months)
    
    string_init = str(int(min_year)) + "-" + str(int(min_month))
    string_final = str(int(max_year)) + "-" + str(int(max_month))
    years_range = pd.date_range(string_init, string_final, freq='MS').strftime("%Y").tolist()
    months_range = pd.date_range(string_init, string_final, freq='MS').strftime("%m").tolist()
    
    date_range = pd.DataFrame(zip(years_range, months_range))

    return date_range


# headers from data_month that will be used
info_needed = ['upc','dma_code', 'year', 'month', 'sales', 'volume']

# must have 4 ../../../.. because i'm inside a folder inside Main
df = (pd.read_csv('../../../../All/m_' + code + '/intermediate/data_month.csv'))

# pivoting the dmas and salving sales and volume for each upc year month
pivoted = df.pivot_table(index = ['upc','year','month'], columns = 'dma_code', values = ['volume','sales']).reset_index()

# filling in for 0
pivoted.fillna(0)

pivoted.to_csv('/projects/b1048/gillanes/Mergers/Codes/Mergers/Main/MarinaMurphy/pivoted_data.csv', index = False, sep = ',', encoding = 'utf-8')

# opening the dataframe and using only info needed


short_data_month1 = (pd.read_csv('../../../../All/m_' + code + '/intermediate/data_month.csv'))
short_data_month=short_data_month1[info_needed]


short_data_month1 = (pd.read_csv('../../../../All/m_' + code + '/intermediate/data_month.csv'))
short_data_month=short_data_month1[info_needed]

short_data_month = (pd.read_csv('../../../All/m_' + code + '/intermediate/data_month.csv')[info_needed]
>>>>>>> 5550b0308ccf965739b2579447eafec2aea8f410

# saving as new file
short_data_month.to_csv('/projects/b1048/gillanes/Mergers/Codes/Mergers/Main/MarinaMurphy/pivoted_datacsv', index = False, sep = ',', encoding = 'utf-8')

log_out = open('try_1.log', 'w')
log_err = open('try_1.err', 'w')
sys.stdout = log_out
sys.stderr = log_err


#getting the owners from aux
# def append_owners(code, df, month_or_quarter,add_dhhi = False):
# 	# Load list of UPCs and brands
# 	upcs = pd.read_csv('../../../../All/m_' + code + '/intermediate/upcs.csv', delimiter = ',', index_col = 'upc')
# 	upcs = upcs['brand_code_uc']
# 	upc_map = upcs.to_dict()

# 	# Map brands to dataframe (by UPC)
# 	df['brand_code_uc'] = df['upc'].map(upc_map)

# 	# Load ownership assignments
# 	brand_to_owner = pd.read_csv('../../../../All/m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')

# 	# Assign min/max year and month when listed as zero in ownership mapping
# 	min_year = df['year'].min()
# 	max_year = df['year'].max()

# 	if month_or_quarter == 'month':
# 		min_month = df.loc[df['year']==min_year,'month'].min()
# 		max_month = df.loc[df['year']==max_year,'month'].max()
# 	elif month_or_quarter == 'quarter':
# 		min_month = (3*(df.loc[df['year']==min_year,'quarter']-1)+1).min()
# 		max_month = (3*df.loc[df['year']==max_year,'quarter']).max()

# 	# Remove Onwership that starts later than the latest time in the dataframe
# 	brand_to_owner = brand_to_owner[(brand_to_owner['start_year'] < max_year) | ((brand_to_owner['start_year'] == max_year)&(brand_to_owner['start_month'] <= max_month))]
# 	# Remove Onwership that ends earlier than the earliest time in the dataframe
# 	brand_to_owner = brand_to_owner[(brand_to_owner['end_year'] > min_year) | ((brand_to_owner['end_year'] == min_year)&(brand_to_owner['end_month'] >= min_month)) | (brand_to_owner['end_year'] == 0)]

# 	brand_to_owner.loc[(brand_to_owner['start_month']==0) | (brand_to_owner['start_year']<min_year) | ((brand_to_owner['start_year']==min_year)&(brand_to_owner['start_month']<min_month)),'start_month'] = min_month
# 	brand_to_owner.loc[(brand_to_owner['start_year']==0) | (brand_to_owner['start_year']<min_year),'start_year'] = min_year
# 	brand_to_owner.loc[(brand_to_owner['end_month']==0) | (brand_to_owner['end_year']>max_year) | ((brand_to_owner['end_year']==max_year)&(brand_to_owner['end_month']>max_month)),'end_month'] = max_month
# 	brand_to_owner.loc[(brand_to_owner['end_year']==0) | (brand_to_owner['end_year']>max_year),'end_year'] = max_year

# 	# Throw error if (1) dates don't span the entirety of the sample period or
# 	# (2) ownership dates overlap
# 	brand_to_owner_test = brand_to_owner.copy()
# 	brand_to_owner_test = brand_to_owner_test.sort_values(by=['brand_code_uc', 'start_year', 'start_month'])

# 	if month_or_quarter == 'month':
# 		min_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).min()
# 		max_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).max()
# 		brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
# 		brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))
# 	elif month_or_quarter == 'quarter':
# 		min_date = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1)).min()
# 		max_date = pd.to_datetime(dict(year=df.year, month=3*df.quarter, day=1)).max()
# 		brand_to_owner_test.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner_test['start_month']/3)-1)+1
# 		brand_to_owner_test.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, brand_to_owner_test.end_year, brand_to_owner_test.end_year - 1)
# 		brand_to_owner_test.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, 3*(np.floor(brand_to_owner_test.end_month/3)), 12)
# 		brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
# 		brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))

# 	brand_dates = brand_to_owner_test.groupby('brand_code_uc')[['start_date_test', 'end_date_test']].agg(['min', 'max'])
# 	if ((brand_dates.start_date_test['min']!=min_date).sum() + (brand_dates.end_date_test['max']!=max_date).sum() > 0):
# 		print('Ownership definitions does not span the entire sample period:')
# 		for index, row in brand_dates.iterrows():
# 			if row.start_date_test['min'] != min_date or row.end_date_test['max'] != max_date:
# 				print(index)
# 				print('start_date: ', row.start_date_test['min'])
# 				print('end_date: ', row.end_date_test['max'])

# 	brand_to_owner_test['owner_num'] = brand_to_owner_test.groupby('brand_code_uc').cumcount()+1
# 	max_num_owner = brand_to_owner_test['owner_num'].max()
# 	brand_to_owner_test = brand_to_owner_test.set_index('owner_num',append=True)
# 	brand_to_owner_test = brand_to_owner_test.unstack('owner_num')
# 	brand_to_owner_test.columns = ['{}_{}'.format(var, num) for var, num in brand_to_owner_test.columns]

# 	for ii in range(2,max_num_owner+1):
# 		overlap_or_gap = (brand_to_owner_test['start_year_' + str(ii)] < brand_to_owner_test['end_year_' + str(ii-1)]) | \
# 			((brand_to_owner_test['start_year_' + str(ii)] == brand_to_owner_test['end_year_' + str(ii-1)]) & \
# 			(brand_to_owner_test['start_month_' + str(ii)] != (brand_to_owner_test['end_month_' + str(ii-1)] + 1))) | \
# 			((brand_to_owner_test['start_year_' + str(ii)] > brand_to_owner_test['end_year_' + str(ii-1)]) & \
# 			((brand_to_owner_test['start_month_' + str(ii)] != 1) | (brand_to_owner_test['end_month_' + str(ii-1)] != 12)))
# 		if overlap_or_gap.sum() > 0:
# 			brand_to_owner_test['overlap'] = overlap_or_gap
# 			indices = brand_to_owner_test[brand_to_owner_test['overlap'] != 0].index.tolist()
# 			for index in indices:
# 				print(brand_to_owner_test.loc[index])
# 			raise Exception('There are gaps or overlap in the ownership mapping.')

# 	# Merge on brand and date intervals
# 	if month_or_quarter == 'month':
# 		brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
# 		brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
# 		df['date'] = pd.to_datetime(dict(year=df.year, month=df.month, day=1))
# 		if add_dhhi:
# 			sqlcode = '''
# 			select df.upc, df.year, df.month, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
# 			from df
# 			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
# 			'''
# 		else:
# 			sqlcode = '''
# 			select df.upc, df.year, df.month, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
# 			from df
# 			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
# 			'''
# 	elif month_or_quarter == 'quarter':
# 		brand_to_owner.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner['start_month']/3)-1)+1
# 		brand_to_owner.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, brand_to_owner.end_year, brand_to_owner.end_year - 1)
# 		brand_to_owner.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, 3*(np.floor(brand_to_owner.end_month/3)), 12)
# 		brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
# 		brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
# 		df['date'] = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1))
# 		if add_dhhi:
# 			sqlcode = '''
# 			select df.upc, df.year, df.quarter, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
# 			from df
# 			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
# 			'''
# 		else:
# 			sqlcode = '''
# 			select df.upc, df.year, df.quarter, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
# 			from df
# 			inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
# 			'''
# 	df_own = ps.sqldf(sqlcode,locals())


# 	return df_own


# df_own = append_owners(code, df_pre, month_or_quarter, add_dhhi = True)
# df_own['owner']

# # Iterate through items of list1
# for upc_month_DMA in short_data_month:
#     # Iterate through items of list2
#     for i in range(len(df_own)):
#         # Match 'Name' field in list1 to 'Name' field in list2
#         # Is UPC one of the keys/columns in df_own output object from the aux program?
#         if upc_month_DMA[0] == df_own['upc']:
#             # Add owner to that short_data_month item
#             short_data_month[i] = short_data_month[i] + (df_own['owner'], )

