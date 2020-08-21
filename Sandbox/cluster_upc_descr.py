import re
import sys
from datetime import datetime
import pyblp
import pickle
import pandas as pd
import numpy as np
import pandasql as ps
import os
from ../Main import auxiliary as aux


# def get_product_map(groups):
# 	products_path = "../../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
# 	products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0, index_col = ["upc","upc_ver_uc"])
# 	int_groups = [int(i) for i in groups]
# 	wanted_products = products[products['product_group_code'].isin(int_groups)]
# 	product_map = wanted_products
# 	return product_map

# test with merger ID 3035705020_13, Cosmetics-nail polish,
