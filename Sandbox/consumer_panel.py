import re
import sys
from datetime import datetime
import auxiliary as aux
from tqdm import tqdm
import numpy as np
import pandas as pd
from clean_data import clean_data
import os


def parse_info(code):

	file = open('../../../All/' + code + '/info.txt', mode = 'r')
	info_file = file.read()
	file.close()

	all_info_elements = re.finditer('\[(.*?):(.*?)\]', info_file, re.DOTALL)
	info_dict = {}

	for info in all_info_elements:
		info_name = info.group(1).strip()
		info_content = info.group(2).strip()
		info_dict[info_name] = info_content

	return info_dict


def upc_list(code):

	# get a list of the selected upcs for the merger

	path_input = "../../../All/" + code + "/intermediate"
	data = pd.read_csv(path_input + "/upcs.csv")
	data = data[data['upc', 'brand_code_uc', 'module']]

	return upc_list


def merge(code, upc_list):

	# stata: merge m:1 upc using "upc_list.dta"

	trips_upc = pd.DataFrame()

	for year in years:

		purchase_path = "../../../Data/Consumer_Panel/nielsen_extracts/HMS/" + str(year) + "/Annual_Files/purchases_" + str(year) + ".tsv"
		trip_path = "../../../Data/Consumer_Panel/nielsen_extracts/HMS/" + str(year) + "/Annual_Files/trips_" + str(year) + ".tsv"

		df_purchase = pd.read_csv(purchase_path, sep='\t')
		df_trips = pd.read_csv(trip_path, sep='\t')

		df_purchase = pd.merge(df_purchase, upc_list, on=['upc'], how='inner')
		df_trips = pd.merge(df_purchase, df_trips, on=['trip_code_uc'], how='inner')

		trips_upc = trips_upc.append(df_trips)
		trips_upc['month'] = trips_upc['date'][5:7]
		trips_upc['year'] = trips_upc['date'][0:4]

	purchase_counts = trips_upc.groupby(['household_code_uc', 'year', 'month', 'upc']).size().reset_index(name='counts')
	purchase_counts.to_csv("../../../All/" + code + "/intermediate/purchase_counts.csv")



folder = sys.argv[1]
code = 'm_' + folder

log_out = open('output/consumer_panel.log', 'w')
log_err = open('output/consumer_panel.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

info_dict = parse_info(code)
groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
groups = [str(0) + str(group) if len(str(group)) == 3 else group for group in groups]
years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

upcs = upc_list(code)









