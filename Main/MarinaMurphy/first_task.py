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

def int_to_month(value):
        year = np.floor((value - 1) / 12)
        month = value - 12 * year
        return year, month

def totuple(a):
    try:
        return tuple(totuple(i) for i in a)
    except TypeError:
        return a

# parsing info.txt file, returns dictionary of info
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

# getting the parties from the info dictionary, but you must use
# get_parties(info_dict["MergingParties"]) so info_str = info_dict["MergingParties"]
def get_parties(info_str):
    all_parties = re.finditer('{(.*?)}', info_str, re.DOTALL)
    merging_parties = []
    for i in all_parties:
        merging_parties.append(i.group(1).strip())
    return merging_parties

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

#getting the owners from aux

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

    
    ### Part 2: extracting ownership using full df with all upc-year-month-dma combinations
    df_own = append_owners(code, empty_to_merge_dma_full, 'month')

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

    # extract merging parties
    merging_parties = get_parties(info_dict["MergingParties"])
    
    #assign 1's if owner = merging parties
    pivoted.loc[pivoted['owner'].isin(merging_parties), 'merging_party'] = 1
    
    # extracting year and month of date completed
    year = int((info_dict['DateCompleted'])[:4])
    month = int((info_dict['DateCompleted'])[5:7])
    
    # setting = 1 if month and year are greater than date completed for the merging parties
    pivoted.loc[(pivoted['merging_party'] == 1) & (pivoted['year'] >= year) & (pivoted['month'] >= month), 'post_merger'] = 1
    
    pivoted.loc[(pivoted['merging_party'] == 1) & (pivoted['year'] > year), 'post_merger'] = 1
    pivoted.loc[(pivoted['merging_party'] == 1) & (pivoted['year'] == year) & (pivoted['month'] >= month), 'post_merger'] = 1
    
    # export to csv
    pivoted.to_csv('m_' + code +'/pivoted_data.csv', index = False, sep = ',', encoding = 'utf-8')
    
    log_out = open('try_1.log', 'w')
    log_err = open('try_1.err', 'w')
    sys.stdout = log_out
    sys.stderr = log_err
    
    return pivoted


codes = ['1924129020_1', '2641303020_8', '2823116020_9']

for code in codes:
    os.mkdir('m_' + code)
    table_1(code)