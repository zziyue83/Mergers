import re
import sys
import auxiliary as aux
from tqdm import tqdm
import pandas as pd

def load_store_table(year):
	store_path = "../../../Data/nielsen_extracts/RMS/" + year + "/Annual_Files/stores_" + year + ".tsv"
	store_table = pd.read_csv(store_path, delimiter = "\t", index_col = "store_code_uc")
	print("Loaded store file of "+ year)
	return store_table


def get_store_brands(code, years, groups, modules, month_or_quarter = 'month'):

    product_map = aux.get_product_map(list(set(groups)))
    product_map = product_map.reset_index()[['upc','brand_code_uc','brand_descr']].drop_duplicates()
    parent_upc_list = []
    store_brands_list = []

    for year in years:
        store_table = load_store_table(year)
        store_map = store_table.to_dict()
        parent_map = store_map['parent_code']
        upc_ver_map = aux.get_upc_ver_uc_map(year)

        for group, module in zip(groups, modules):
            movement_table = aux.load_chunked_year_module_movement_table(year, group, module)

            for data_chunk in tqdm(movement_table):
                data_chunk['parent_code'] = data_chunk['store_code_uc'].map(parent_map)
                parent_upc = data_chunk.join(product_map.set_index('upc'), on=['upc'], how='outer')
                parent_upc = parent_upc[['parent_code','upc','brand_code_uc','brand_descr']].dropna(subset=['parent_code']).drop_duplicates()
                parent_upc_list.append(parent_upc)

    parent_upc = pd.concat(parent_upc_list)
    parent_upc_grouped = parent_upc[['parent_code','upc','brand_code_uc','brand_descr']].drop_duplicates().groupby('upc')

    for upc, parent_upc_group in parent_upc_grouped:
        if len(list(set(parent_upc_group.parent_code))) == 1:
            store_brands_list.append(parent_upc_group)

    store_brands = pd.concat(store_brands_list)
    print(store_brands.head())

    base_folder = '../../../All/m_' + code + '/intermediate/'
    store_brands.to_csv(base_folder + 'store_brands.csv', index = False, sep = ',', encoding = 'utf-8')


code = sys.argv[1]
log_out = open('../../../All/m_' + code + '/output/store_brands.log', 'w')
log_err = open('../../../All/m_' + code + '/output/store_brands.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = aux.parse_info(code)
groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

get_store_brands = get_store_brands(code, years, groups, modules)

log_out.close()
log_err.close()