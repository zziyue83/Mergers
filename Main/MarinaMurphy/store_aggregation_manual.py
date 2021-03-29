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

code = '2641303020_8'
info_dict = parse_info(code)
info_dict.keys()
final_unit = info_dict['FinalUnits']

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

# make conversion map
conversion_map = get_conversion_map(code, info_dict["FinalUnits"])
    
area_month_upc = aggregate_movement(code, years, groups, modules, "month", conversion_map, info_dict["DateAnnounced"], info_dict["DateCompleted"])
area_month_upc = pd.DataFrame.from_records(area_time_upc, columns = ['store_code_uc', 'upc', 'units', 'prmult', 'price', 'feature','display', 
    'year', 'month', 'dma_code', 'sales', 'module', 'upc_ver_uc','brand_code_uc', 'brand_descr', 'multi', 'size1_units', 'size1_amount', 
    'conversion', 'volume', 'prices', 'total_sales', 'market_size','shares'])

print(type(area_month_upc))

#area_month_upc = pd.DataFrame.from_records(area_month_upc)

# creating area_month_upc file
area_month_upc = area_month_upc[['store_code_uc', 'upc', 'year', 'month', 'sales', 'dma_code', 'volume']]
print(type(area_month_upc))

# loading stores
store_map.to_csv("store_map.csv")

# inserting store type
area_month_upc.insert(1, "channel_code", area_month_upc["store_code_uc"].map(store_map["channel_code"]))
area_month_upc.insert(1, "parent_code", area_month_upc["store_code_uc"].map(store_map["parent_code"]))

area_month_upc.to_csv('area_month.csv')

area_month_upc = area_month_upc.groupby(['channel_code','upc','year','month']).agg({'sales': 'sum', 'volume': 'sum'})
area_month_upc = area_month_upc.pivot_table(index = ['upc','year','month'], columns = 'channel_code', values = ['sales','volume']).reset_index()

area_month_upc.to_csv('area_month_with_channelcodes.csv')


