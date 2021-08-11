import subprocess
import os
import re
import sys
import pandas as pd
import unicodecsv as csv
import auxiliary as aux

def get_conversion_map(code, final_unit, method = 'mode'):
    # Get in the conversion map -- size1_units, multiplication
    master_conversion = pd.read_csv('../../../All/master/unit_conversion.csv')
    assert master_conversion['final_unit'].str.contains(final_unit).any(), "Cannot find %r as a final_unit" % final_unit
    master_conversion = master_conversion[master_conversion['final_unit'] == final_unit]

    these_units = pd.read_csv('../../../All/m_' + code + '/properties/units_edited.csv')
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
    print(these_units)

    conversion_map = these_units.to_dict()
    return conversion_map

def CV(folder, month_or_quarter='month'):

    merger_folder = folder + '/output'

    code = folder[15:]
    info_dict = aux.parse_info(code)
    year = info_dict['DateCompleted'][0:4]
    month = str(int(info_dict['DateCompleted'][5:7]))
    path_input = folder + "/intermediate"

    '''
    Silenced lines from when we needed to add variables to the
    demand_month.csv datasets.

    df2 = pd.read_csv(path_products + "products.tsv", sep="\t", engine = 'python', quotechar='"', error_bad_lines=False)
    df = pd.merge(df, df2, on='upc')
    df = df.drop(['upc_ver_uc', 'upc_descr', 'product_module_code', 'product_module_descr',
                     'product_group_code', 'product_group_descr', 'department_code',
                     'department_descr', 'brand_descr', 'dataset_found_uc', 'brand_code_uc_y',
                     'size1_change_flag_uc'], axis=1)

    df.to_csv(path_input + '/demand_month.csv',
                  sep=',', encoding='utf-8', index=False)

    conversion_map = get_conversion_map(code, info_dict["FinalUnits"])
    df = pd.read_csv(path_input + "/demand_month.csv", sep=",")
    df['conversion'] = df['size1_units'].map(conversion_map['conversion'])
    df.to_csv(path_input + '/demand_month.csv',
                  sep=',', encoding='utf-8', index=False)

    '''

    if not os.path.isdir(folder + '/output/tables'):
        os.makedirs(folder + '/output/tables')

    # change dofile path between cross_valid.do and cross_valid_stats.do
    dofile = "/projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox/cross_valid_stats.do"
    DEFAULT_STATA_EXECUTABLE = "/software/Stata/stata14/stata-mp"
    path_products = folder + "/../../Data/nielsen_extracts/RMS/Master_Files/Latest/"


    path_output = "../output"
    print(folder)
    cmd = [DEFAULT_STATA_EXECUTABLE, "-b", "do", dofile, path_input, path_output, year, month]
    subprocess.call(cmd)



folder = sys.argv[1]
log_out = open('output/CV_data.log', 'a')
log_err = open('output/CV_data.err', 'a')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'

if os.path.exists(folder + '/intermediate/demand_month.csv'):
    print(folder)
    CV(folder)
