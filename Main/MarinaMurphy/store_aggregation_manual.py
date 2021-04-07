import pandas as pd
import sys
import csv
from datetime import datetime, timedelta
from collections import OrderedDict
import numpy as np
import time
import pyblp
import auxiliary as aux
import sqldf
import pysqldf as ps
from pandasql import sqldf
import pandasql
import os
import re
import itertools
import shutil
from tqdm import tqdm
from clean_data import clean_data

def int_to_month(value):
        year = np.floor((value - 1) / 12)
        month = value - 12 * year
        return year, month

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

def load_store_table(year):
    store_path = "../../../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
    store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
    print("Loaded store file of "+ year)
    return store_table

def get_product_map(groups):
    products_path = "../../../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
    products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = ["upc","upc_ver_uc"])
    int_groups = [int(i) for i in groups]
    wanted_products = products[products['product_group_code'].isin(int_groups)]
    product_map = wanted_products
    return product_map

def get_upc_ver_uc_map(year):
    upc_ver_path = "../../../../Data/nielsen_extracts/RMS/"+str(year)+"/Annual_Files/rms_versions_"+str(year)+".tsv"
    upc_vers = pd.read_csv(upc_ver_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = "upc")
    upc_vers = upc_vers['upc_ver_uc']
    upc_ver_map = upc_vers.to_dict()
    return upc_ver_map

def get_conversion_map(code, final_unit, method = 'mode'):
    # Get in the conversion map -- size1_units, multiplication
    master_conversion = pd.read_csv('../../../../All/master/unit_conversion.csv')
    assert master_conversion['final_unit'].str.contains(final_unit).any(), "Cannot find %r as a final_unit" % final_unit
    master_conversion = master_conversion[master_conversion['final_unit'] == final_unit]

    these_units = pd.read_csv('../../../../All/m_' + code + '/properties/units_edited.csv')
    these_units['conversion'] = 0

# Anything that has convert = 1 must be in the master folder
    convertible = these_units.loc[these_units.convert == 1].copy()
    for this_unit in convertible.units.unique():
        assert master_conversion['initial_unit'].str.contains(this_unit).any(), "Cannot find %r as an initial_unit" % this_unit
        if this_unit in master_conversion.initial_unit.unique():
            convert_factor = master_conversion.conversion[master_conversion.initial_unit == this_unit].values
            these_units.loc[these_units.units == this_unit, 'conversion'] = convert_factor
            convertible.loc[convertible.units == this_unit, 'conversion'] = convert_factor

    # Convert the total quantity
    convertible['total_quantity'] = convertible['total_quantity'] * convertible['conversion']

    # The "method" for convert = 0 is mapped to the "method" for the convert = 1
    # with the largest quantity
    where_largest = convertible.total_quantity.idxmax()
    if method == 'mode':
        base_size = convertible.loc[where_largest]['mode']
        other_size = these_units[these_units.convert == 0]['mode']
    else:
        base_size = convertible.loc[where_largest]['median']
        other_size = these_units[these_units.convert == 0]['median']

    these_units.conversion[these_units.convert == 0] = convertible.conversion[where_largest] * base_size / other_size
    these_units = these_units[['units', 'conversion']]
    these_units = these_units.rename(columns = {'units' : 'size1_units'})
    these_units = these_units.set_index('size1_units')

    conversion_map = these_units.to_dict()
    return conversion_map
def load_chunked_year_module_movement_table(year, group, module, path = ''):
    if path == '':
        path = "../../../../Data/nielsen_extracts/RMS/" + year + "/Movement_Files/" + group + "_" + year + "/" + module + "_" + year + ".tsv"
    assert os.path.exists(path), "File does not exist: %r" % path
    table = pd.read_csv(path, delimiter = "\t", chunksize = 10000000)
    return table

def aggregate_movement(code, years, groups, modules, month_or_quarter, conversion_map, merger_start_date, merger_stop_date, market_size_scale = 1.5, pre_months = 24, post_months = 24):

# Get the relevant range
    stop_dt = datetime.strptime(merger_stop_date, '%Y-%m-%d')
    start_dt = datetime.strptime(merger_start_date, '%Y-%m-%d')
    stop_month_int = stop_dt.year * 12 + stop_dt.month
    start_month_int = start_dt.year * 12 + start_dt.month

    min_year, min_month = aux.int_to_month(start_month_int - pre_months)
    max_year, max_month = aux.int_to_month(stop_month_int + post_months)
    min_quarter = np.ceil(min_month/3)
    max_quarter = np.ceil(max_month/3)

    #manual fix for baby strained food
    if ((code=='1817013020_3') & (max_year > 2008)):
        max_year = 2008
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2008, years))

    #manual fix for bread
    if ((code=='2203820020_1') & (max_year > 2012)):
        max_year = 2012
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2012, years))

    #manual fix for buns
    if ((code=='2203820020_2') & (max_year > 2012)):
        max_year = 2012
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2012, years))

    #manual fix for rolls
    if ((code=='2203820020_3') & (max_year > 2012)):
        max_year = 2012
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2012, years))

    #manual fix for pies
    if ((code=='2203820020_8') & (max_year > 2012)):
        max_year = 2012
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2012, years))

    #manual fix for bakery remaining
    if ((code=='2203820020_10') & (max_year > 2012)):
        max_year = 2012
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2012, years))

    #manual fix for cheesecake
    if ((code=='2203820020_11') & (max_year > 2012)):
        max_year = 2012
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2012, years))

    #manual fix for biscuits
    if ((code=='2203820020_12') & (max_year > 2012)):
        max_year = 2012
        max_month = 12
        max_quarter = 4
        years = list(filter(lambda x: int(x) <= 2012, years))

        #manual fix for RBC_Bread
    if ((code=='2033113020_2') & (min_year < 2007)):
        min_year = 2007
        min_month = 1
        min_quarter = 1
        years = list(filter(lambda x: int(x) >= 2007, years))

        #manual fix for RBC_Cake
    if ((code=='2033113020_3') & (min_year < 2007)):
        min_year = 2007
        min_month = 1
        min_quarter = 1
        years = list(filter(lambda x: int(x) >= 2007, years))

        #manual fix for Headache pills
    if ((code=='2373087020_1') & (min_year < 2010)):
        min_year = 2010
        min_month = 1
        min_quarter = 1
        years = list(filter(lambda x: int(x) >= 2010, years))

        #manual fix for School and Office Supplies
    if ((code=='2363232020_4') & (min_year < 2010)):
        min_year = 2010
        min_month = 1
        min_quarter = 1
        years = list(filter(lambda x: int(x) >= 2010, years))

    area_time_upc_list = []
    product_map = get_product_map(list(set(groups)))
    add_from_map = ['brand_code_uc', 'brand_descr', 'multi', 'size1_units', 'size1_amount']
    aggregation_function = {'week_end' : 'first', 'units' : 'sum', 'prmult' : 'mean', 'price' : 'mean', 'feature' : 'first', 'display' : 'first', 'store_code_uc' : 'first', 'sales' : 'sum', 'module' : 'first'}

    for year in years:
        store_table = load_store_table(year)
        store_map = store_table.to_dict()
        dma_map = store_map['dma_code']
        upc_ver_map = get_upc_ver_uc_map(year)

        for group, module in zip(groups, modules):
            movement_table = load_chunked_year_module_movement_table(year, group, module)

            for data_chunk in tqdm(movement_table):
                data_chunk['year'] = np.floor(data_chunk['week_end']/10000)
                data_chunk['year'] = data_chunk['year'].astype(int)
                if month_or_quarter == "month":
                    data_chunk[month_or_quarter] = np.floor((data_chunk['week_end'] % 10000)/100)
                    data_chunk[month_or_quarter] = data_chunk[month_or_quarter].astype(int)

                    if int(year) == min_year:
                        data_chunk = data_chunk[data_chunk.month >= min_month]
                    elif int(year) == max_year:
                        data_chunk = data_chunk[data_chunk.month <= max_month]
                elif month_or_quarter == "quarter":
                    data_chunk[month_or_quarter] = np.ceil(np.floor((data_chunk['week_end'] % 10000)/100)/3)
                    data_chunk[month_or_quarter] = data_chunk[month_or_quarter].astype(int)
                    if int(year) == min_year:
                        data_chunk = data_chunk[data_chunk.quarter >= min_quarter]
                    elif int(year) == max_year:
                        data_chunk = data_chunk[data_chunk.quarter <= max_quarter]

                data_chunk['dma_code'] = data_chunk['store_code_uc'].map(dma_map)
                data_chunk['sales'] = data_chunk['price'] * data_chunk['units'] / data_chunk['prmult']
                data_chunk['module'] = int(module)
                data_chunk['upc_ver_uc'] = data_chunk['upc'].map(upc_ver_map)
                area_time_upc = data_chunk.groupby(['year', month_or_quarter, 'upc', 'upc_ver_uc', 'dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = data_chunk.columns)
                area_time_upc_list.append(area_time_upc)

    area_time_upc = pd.concat(area_time_upc_list)
    area_time_upc = area_time_upc.groupby(['year', month_or_quarter, 'upc', 'upc_ver_uc', 'dma_code'], as_index = False).aggregate(aggregation_function).reindex(columns = area_time_upc.columns)
    area_time_upc = area_time_upc.join(product_map[add_from_map], on=['upc','upc_ver_uc'], how='left')
    area_time_upc = clean_data(code, area_time_upc)
    area_time_upc['conversion'] = area_time_upc['size1_units'].map(conversion_map['conversion'])
    area_time_upc['volume'] = area_time_upc['units'] * area_time_upc['size1_amount'] * area_time_upc['multi'] * area_time_upc['conversion']
    area_time_upc['prices'] = area_time_upc['sales'] / area_time_upc['volume']

    #area_time_upc.drop(['week_end','store_code_uc'], axis=1, inplace=True)

    # Normalize the prices by the CPI.  Let January 2010 = 1.
    area_time_upc = aux.adjust_inflation(area_time_upc, ['prices', 'sales'], month_or_quarter)

    # Get the market sizes here, by summing volume within dma-time and then taking 1.5 times max within-dma
    short_area_time_upc = area_time_upc[['dma_code', 'year', month_or_quarter, 'volume', 'sales']]
    market_sizes = short_area_time_upc.groupby(['dma_code', 'year', month_or_quarter]).sum()
    market_sizes['market_size'] = market_size_scale * market_sizes['volume'].groupby('dma_code').transform('max')
    market_sizes = market_sizes.rename(columns = {'sales': 'total_sales', 'volume' : 'total_volume'})

    # Save the output if this is month
    if month_or_quarter == 'month':
        market_sizes.to_csv('../../../../All/m_' + code + '/intermediate/market_sizes.csv', sep = ',', encoding = 'utf-8')

    # Shares = volume / market size.  Map market sizes back and get shares.
    area_time_upc = area_time_upc.join(market_sizes.drop('total_volume', axis=1), on = ['dma_code', 'year', month_or_quarter])
    area_time_upc['shares'] = area_time_upc['volume'] / area_time_upc['market_size']

    return area_time_upc, store_map

def store_aggregation(code):
    info_dict = parse_info(code)
    info_dict.keys()
    final_unit = info_dict['FinalUnits']

    groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
    years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

    # make conversion map
    conversion_map = get_conversion_map(code, info_dict["FinalUnits"])
        
    area_month_upc, store_map = aggregate_movement(code, years, groups, modules, "month", conversion_map, info_dict["DateAnnounced"], info_dict["DateCompleted"])

    #area_month_upc = pd.DataFrame.from_records(area_month_upc, columns = ['store_code_uc', 'upc', 'units', 'prmult', 'price', 'feature','display', 
     #   'year', 'month', 'dma_code', 'sales', 'module', 'upc_ver_uc','brand_code_uc', 'brand_descr', 'multi', 'size1_units', 'size1_amount', 
      #  'conversion', 'volume', 'prices', 'total_sales', 'market_size','shares'])

    print(type(area_month_upc))

    #area_month_upc = pd.DataFrame.from_records(area_month_upc)

    # creating area_month_upc file
    area_month_upc = area_month_upc[['store_code_uc', 'upc', 'year', 'month', 'sales', 'dma_code', 'volume']]

    # loading stores
    #store_map.to_csv("store_map.csv")

    # inserting store type
    area_month_upc.insert(1, "channel_code", area_month_upc["store_code_uc"].map(store_map["channel_code"]))
    area_month_upc.insert(1, "parent_code", area_month_upc["store_code_uc"].map(store_map["parent_code"]))

    area_month_upc.to_csv('m_' + code + '/area_month.csv')

    area_month_upc = area_month_upc.groupby(['channel_code','upc','year','month']).agg({'sales': 'sum', 'volume': 'sum'})
    area_month_upc = area_month_upc.pivot_table(index = ['upc','year','month'], columns = 'channel_code', values = ['sales','volume'], fill_value = 0).reset_index()

    area_month_upc.to_csv('m_' + code + '/area_month_with_channelcodes.csv')
    
    return area_month_upc

def append_owners(code, df, month_or_quarter,add_dhhi = False):
    # Load list of UPCs and brands
    upcs = pd.read_csv('../../../../All/m_' + code + '/intermediate/upcs.csv', delimiter = ',', index_col = 'upc')
    upcs = upcs['brand_code_uc']
    upc_map = upcs.to_dict()

# # Map brands to dataframe (by UPC)
    df['brand_code_uc'] = df['upc'].map(upc_map)

# Load ownership assignments
    brand_to_owner = pd.read_csv('../../../../All/m_' + code + '/properties/ownership.csv', delimiter = ',', index_col = 'brand_code_uc')

# Assign min/max year and month when listed as zero in ownership mapping
    min_year = df['year'].min()
    max_year = df['year'].max()

    if month_or_quarter == 'month':
        min_month = df.loc[df['year']==min_year,'month'].min()
        max_month = df.loc[df['year']==max_year,'month'].max()
    elif month_or_quarter == 'quarter':
        min_month = (3*(df.loc[df['year']==min_year,'quarter']-1)+1).min()
        max_month = (3*df.loc[df['year']==max_year,'quarter']).max()

    # Remove Onwership that starts later than the latest time in the dataframe
    brand_to_owner = brand_to_owner[(brand_to_owner['start_year'] < max_year) | ((brand_to_owner['start_year'] == max_year)&(brand_to_owner['start_month'] <= max_month))]
    # Remove Onwership that ends earlier than the earliest time in the dataframe
    brand_to_owner = brand_to_owner[(brand_to_owner['end_year'] > min_year) | ((brand_to_owner['end_year'] == min_year)&(brand_to_owner['end_month'] >= min_month)) | (brand_to_owner['end_year'] == 0)]

    brand_to_owner.loc[(brand_to_owner['start_month']==0) | (brand_to_owner['start_year']<min_year) | ((brand_to_owner['start_year']==min_year)&(brand_to_owner['start_month']<min_month)),'start_month'] = min_month
    brand_to_owner.loc[(brand_to_owner['start_year']==0) | (brand_to_owner['start_year']<min_year),'start_year'] = min_year
    brand_to_owner.loc[(brand_to_owner['end_month']==0) | (brand_to_owner['end_year']>max_year) | ((brand_to_owner['end_year']==max_year)&(brand_to_owner['end_month']>max_month)),'end_month'] = max_month
    brand_to_owner.loc[(brand_to_owner['end_year']==0) | (brand_to_owner['end_year']>max_year),'end_year'] = max_year

    # Throw error if (1) dates don't span the entirety of the sample period or
    # (2) ownership dates overlap
    brand_to_owner_test = brand_to_owner.copy()
    brand_to_owner_test = brand_to_owner_test.sort_values(by=['brand_code_uc', 'start_year', 'start_month'])
    
    if month_or_quarter == 'month':
        min_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).min()
        max_date = pd.to_datetime(dict(year=df.year, month=df.month, day=1)).max()
        brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
        brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))
    elif month_or_quarter == 'quarter':
        min_date = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1)).min()
        max_date = pd.to_datetime(dict(year=df.year, month=3*df.quarter, day=1)).max()
        brand_to_owner_test.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner_test['start_month']/3)-1)+1
        brand_to_owner_test.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, brand_to_owner_test.end_year, brand_to_owner_test.end_year - 1)
        brand_to_owner_test.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner_test.end_month/3)) > 0, 3*(np.floor(brand_to_owner_test.end_month/3)), 12)
        brand_to_owner_test['start_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.start_year, month=brand_to_owner_test.start_month, day=1))
        brand_to_owner_test['end_date_test'] = pd.to_datetime(dict(year=brand_to_owner_test.end_year, month=brand_to_owner_test.end_month, day=1))

    brand_dates = brand_to_owner_test.groupby('brand_code_uc')[['start_date_test', 'end_date_test']].agg(['min', 'max'])
    if ((brand_dates.start_date_test['min']!=min_date).sum() + (brand_dates.end_date_test['max']!=max_date).sum() > 0):
        print('Ownership definitions does not span the entire sample period:')
        for index, row in brand_dates.iterrows():
            if row.start_date_test['min'] != min_date or row.end_date_test['max'] != max_date:
                print(index)
                print('start_date: ', row.start_date_test['min'])
                print('end_date: ', row.end_date_test['max'])

    brand_to_owner_test['owner_num'] = brand_to_owner_test.groupby('brand_code_uc').cumcount()+1
    max_num_owner = brand_to_owner_test['owner_num'].max()
    brand_to_owner_test = brand_to_owner_test.set_index('owner_num',append=True)
    brand_to_owner_test = brand_to_owner_test.unstack('owner_num')
    brand_to_owner_test.columns = ['{}_{}'.format(var, num) for var, num in brand_to_owner_test.columns]

    for ii in range(2,max_num_owner+1):
        overlap_or_gap = (brand_to_owner_test['start_year_' + str(ii)] < brand_to_owner_test['end_year_' + str(ii-1)]) | \
            ((brand_to_owner_test['start_year_' + str(ii)] == brand_to_owner_test['end_year_' + str(ii-1)]) & \
            (brand_to_owner_test['start_month_' + str(ii)] != (brand_to_owner_test['end_month_' + str(ii-1)] + 1))) | \
            ((brand_to_owner_test['start_year_' + str(ii)] > brand_to_owner_test['end_year_' + str(ii-1)]) & \
            ((brand_to_owner_test['start_month_' + str(ii)] != 1) | (brand_to_owner_test['end_month_' + str(ii-1)] != 12)))
        if overlap_or_gap.sum() > 0:
            brand_to_owner_test['overlap'] = overlap_or_gap
            indices = brand_to_owner_test[brand_to_owner_test['overlap'] != 0].index.tolist()
            for index in indices:
                print(brand_to_owner_test.loc[index])
            raise Exception('There are gaps or overlap in the ownership mapping.')

    # Merge on brand and date intervals
    if month_or_quarter == 'month':
        brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
        brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
        df['date'] = pd.to_datetime(dict(year=df.year, month=df.month, day=1))
        if add_dhhi:
            sqlcode = '''
            select df.upc, df.year, df.month, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
            from df
            inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
            '''
        else:
            sqlcode = '''
            select df.upc, df.year, df.month, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
            from df
            inner join brand_to_owner on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
            '''
    elif month_or_quarter == 'quarter':
        brand_to_owner.loc[:,'start_month'] = 3*(np.ceil(brand_to_owner['start_month']/3)-1)+1
        brand_to_owner.loc[:,'end_year'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, brand_to_owner.end_year, brand_to_owner.end_year - 1)
        brand_to_owner.loc[:,'end_month'] = np.where(3*(np.floor(brand_to_owner.end_month/3)) > 0, 3*(np.floor(brand_to_owner.end_month/3)), 12)
        brand_to_owner['start_date'] = pd.to_datetime(dict(year=brand_to_owner.start_year, month=brand_to_owner.start_month, day=1))
        brand_to_owner['end_date'] = pd.to_datetime(dict(year=brand_to_owner.end_year, month=brand_to_owner.end_month, day=1))
        df['date'] = pd.to_datetime(dict(year=df.year, month=3*(df.quarter-1)+1, day=1))
        if add_dhhi:
            sqlcode = """
            select 
                df.upc, df.year, df.quarter, df.shares, df.dma_code, df.brand_code_uc, brand_to_owner.owner
            from 
                df
            inner join 
                brand_to_owner 
                    on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
            """
        else:
            sqlcode = """
            select 
                df.upc, df.year, df.quarter, df.prices, df.shares, df.volume, df.dma_code, df.brand_code_uc, df.sales, brand_to_owner.owner
            from 
                df
            inner join 
                brand_to_owner 
                    on df.brand_code_uc=brand_to_owner.brand_code_uc AND df.date >= brand_to_owner.start_date AND df.date <= brand_to_owner.end_date
            """
    df_own = sqldf(sqlcode,locals())

    return df_own

def get_parties(info_str):
    all_parties = re.finditer('{(.*?)}', info_str, re.DOTALL)
    merging_parties = []
    for i in all_parties:
        merging_parties.append(i.group(1).strip())
    return merging_parties


def table_1(code):
    
    # must have 4 ../../../.. because i'm inside a folder inside Main
    # opening data_month file
    df = (pd.read_csv('../../../../All/m_' + code + '/intermediate/data_month.csv'))
    
    ### Part 1: making df complete with year, months and all dma_codes exhaustive
    ### note - df_own does NOT have all dates, only dates which the upc-year-month sales > 0!!
    
    # create list of all year month combinations
    info_dict = parse_info(code)
    date_range = get_date_range(info_dict['DateAnnounced'], info_dict['DateCompleted'], pre_months = 24, post_months = 24)
    
    # calculate number of rows there should be
    upcs = (pd.read_csv('../../../../All/m_' + code + '/intermediate/upcs.csv', delimiter = ','))['upc']
    #total_rows = len(upcs)*len(date_range)
    #total_columns = len(pivoted.columns)
    
    # take upc-year-month-dma combinations now
    repeated_upcs = (pd.concat([upcs]*len(date_range))).sort_values() #ignore_index = True
    repeated_upcs.columns = ['upc']
    repeated_upcs = repeated_upcs.reset_index(drop=True)

    repeated_dates = pd.concat([date_range]*len(upcs))
    repeated_dates.columns = ['year', 'month']
    repeated_dates = repeated_dates.reset_index(drop=True)

    unique_dma_codes = pd.DataFrame(df['dma_code'].unique())
    repeated_dmas = pd.concat([unique_dma_codes]*len(upcs)*len(date_range))
    repeated_dmas.columns = ['dma_code']
    repeated_dmas = repeated_dmas.reset_index(drop=True)

    # creating the empty dataframe with all upc-year-month-dma combinations
    empty_to_merge = pd.concat([pd.concat([repeated_upcs, repeated_dates], axis= 1)]*len(unique_dma_codes))
    empty_to_merge = empty_to_merge.reset_index(drop=True)
    empty_to_merge = empty_to_merge.sort_values(by = ['upc', 'year', 'month'])
    empty_to_merge.insert(1, 'dma_code', repeated_dmas)
    empty_to_merge = empty_to_merge.apply(pd.to_numeric)

    # actual merging with incomplete df, filling in 0's for all spots where no sales
    empty_to_merge_dma_full = pd.merge(df, empty_to_merge, how = "right", on = ['upc', 'dma_code','year', 'month'])
    empty_to_merge_dma_full.fillna(0, inplace=True)

    empty_to_merge_dma_full = empty_to_merge_dma_full.apply(pd.to_numeric)

    # extract merging parties
    merging_parties = get_parties(info_dict["MergingParties"])

    # extracting year and month of date completed
    year = int((info_dict['DateCompleted'])[:4])
    month = int((info_dict['DateCompleted'])[5:7])

    ### Part 2: extracting ownership using full df with all upc-year-month-dma combinations
    df_own = append_owners(code, empty_to_merge_dma_full, 'month')

    df_own['sold_in_usa'] = 0
    df_own.loc[df_own.sales != 0, 'sold_in_usa'] = 1

    df_own['merging_party'] = 0
    df_own['post_merger'] = 0
    
    #assign 1's if owner = merging parties
    df_own.loc[df_own['owner'].isin(merging_parties), 'merging_party'] = 1
    
    # setting = 1 if month and year are greater than date completed for the merging parties
    df_own.loc[(df_own['merging_party'] == 1) & (df_own['year'] >= year) & (df_own['month'] >= month), 'post_merger'] = 1
    
    df_own.loc[(df_own['year'] > year), 'post_merger'] = 1
    df_own.loc[(df_own['year'] == year) & (df_own['month'] >= month), 'post_merger'] = 1

    df_own.to_csv('m_' + code + '/data_month_full.csv')

    # pivoting the dmas and having sales and volume for each upc year month
    pivoted = df_own.pivot_table(index = ['upc','year','month','owner'], columns = 'dma_code', values = ['volume','sales']).reset_index()

    # filling in for 0
    pivoted.fillna(0, inplace=True)
    
    ### Part 3: Additional info
    
    #Total sales of the product in that quarter across the entire US.  Do volume and dollar sales.  For UPCs that aren't sold, it will be 0.
    pivoted.loc[:,'total_sales'] = pivoted[['sales']].sum(axis=1)
    pivoted.loc[:,'total_volume'] = pivoted[['volume']].sum(axis=1)
    
    # dummy for whether product is sold in that month or not in the US
    pivoted['sold_in_usa'] = 0
    pivoted.loc[pivoted.total_sales != 0, 'sold_in_usa'] = 1
    
    # dummies for whether the product is involved in a merger and whether it's post-merger
    # create column of zeroes
    pivoted['merging_party'] = 0
    pivoted['post_merger'] = 0
    
    #assign 1's if owner = merging parties
    pivoted.loc[pivoted['owner'].isin(merging_parties), 'merging_party'] = 1
    
    
    # setting = 1 if month and year are greater than date completed for the merging parties
    pivoted.loc[(pivoted['merging_party'] == 1) & (pivoted['year'] >= year) & (pivoted['month'] >= month), 'post_merger'] = 1
    
    pivoted.loc[(pivoted['year'] > year), 'post_merger'] = 1
    pivoted.loc[(pivoted['year'] == year) & (pivoted['month'] >= month), 'post_merger'] = 1
    
    # export to csv
    pivoted.to_csv('m_' + code +'/pivoted_data.csv', sep = ',', encoding = 'utf-8')
    
    log_out = open('try_1.log', 'w')
    log_err = open('try_1.err', 'w')
    sys.stdout = log_out
    sys.stderr = log_err
    
    return pivoted

code = sys.argv[1]

#code = '2641303020_8'

os.mkdir('m_' + code)
pivoted = table_1(code)
print(len(pivoted['upc'].unique()))

area_month_upc = store_aggregation(code)
print(len(area_month_upc['upc'].unique()))
final_table = pd.merge(pivoted, area_month_upc, how = "left", on = ['upc', 'year', 'month']).fillna(0)
final_table.to_csv('m_' + code + '/final_table.csv')

