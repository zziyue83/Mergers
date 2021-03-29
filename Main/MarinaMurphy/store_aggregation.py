import re
import sys
from datetime import datetime
import auxiliary as aux
from tqdm import tqdm
import numpy as np
import pandas as pd
from clean_data import clean_data

code = '2641303020_8'

info_dict = aux.parse_info(code)

groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

conversion_map = get_conversion_map(code, info_dict["FinalUnits"])
area_month_upc = aggregate_movement(code, years, groups, modules, "month", conversion_map, info_dict["DateAnnounced"], info_dict["DateCompleted"])

conversion_map.to_csv('conversion_map.csv')
aggregate_movement.to_csv('aggregate_movement_removed_store_uc.csv')