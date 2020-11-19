from compute_did_brandlevel import write_overlap, get_major_competitor, did_brandlevel
import os
import sys
import pandas as pd
import auxiliary as aux
from datetime import datetime
import select_products_brandlevel

def run_all_did_brandlevel(base_folder, month_or_quarter='month'):
	# for folder in os.listdir(base_folder):
	# for folder in ['m_1912896020_1']:
	for folder in ['m_2203820020_11']:
		merger_folder = base_folder + '/' + folder + '/output'
		print(merger_folder)
		# print(merger_folder)
		if os.path.exists(merger_folder + '/did_' + month_or_quarter + '.csv') or os.path.exists(merger_folder + "/did_stata_" + month_or_quarter + '_' + '0' + ".csv"):

			# df, characteristics_ls, nest, num_instruments, add_differentiation, add_blp = gather_product_data(code, month_or_quarter)
			# print(df.shape)
			# estimate_demand(code, df, chars = characteristics_ls, nests = nest, month_or_quarter = month_or_quarter, estimate_type = estimate_type,
			#     num_instruments = num_instruments, add_differentiation = add_differentiation, add_blp = add_blp, linear_fe = linear_fe)
			log_out = open(merger_folder + '/compute_did_brandlevel.log', 'w')
			log_err = open(merger_folder + '/compute_did_brandlevel.err', 'w')
			sys.stdout = log_out
			sys.stderr = log_err

			try:

				print(folder)
				code = folder[2:]

				info_dict = aux.parse_info(code)

				# brand-level select product
				groups, modules = aux.get_groups_and_modules(info_dict["MarketDefinition"])
				years = aux.get_years(info_dict["DateAnnounced"], info_dict["DateCompleted"])

				conversion_map = select_products_brandlevel.get_conversion_map(code, info_dict["FinalUnits"])
				area_month_brand = select_products_brandlevel.aggregate_movement(code, years, groups, modules, "month", conversion_map, info_dict["DateAnnounced"], info_dict["DateCompleted"])
				area_quarter_brand = select_products_brandlevel.aggregate_movement(code, years, groups, modules, "quarter", conversion_map, info_dict["DateAnnounced"], info_dict["DateCompleted"])

				if 'InitialShareCutoff' not in info_dict:
					info_dict['InitialShareCutoff'] = 1e-3
				if 'MaxUPC' not in info_dict:
					info_dict['MaxUPC'] = 100
				if 'RegionalShareCutoff' not in info_dict:
					info_dict['RegionalShareCutoff'] = 0.05

				acceptable_brands = select_products_brandlevel.get_acceptable_brands(area_month_brand[['brand_code_uc', 'shares', 'volume']],
					share_cutoff = float(info_dict["InitialShareCutoff"]),
					number_cutoff = int(info_dict["MaxUPC"]),
					regional_share_cutoff = float(info_dict["RegionalShareCutoff"]))

				largest_brand_left_out = select_products_brandlevel.get_largest_brand_left_out(area_month_brand, acceptable_brands)

				# Find the unique brands associated with the acceptable_upcs and spit that out into brands.csv
				# Get the UPC information you have for acceptable_upcs and spit that out into upc_dictionary.csv
				select_products_brandlevel.write_brands_upc(code, area_month_brand, acceptable_brands)

				# Now filter area_month_upc and area_quarter_upc so that only acceptable_upcs survive
				# Print out data_month.csv and data_quarter.csv
				select_products_brandlevel.write_base_dataset(code, area_month_brand, acceptable_brands, 'month')
				select_products_brandlevel.write_base_dataset(code, area_quarter_brand, acceptable_brands, 'quarter')

				# Aggregate data_month (sum shares) by dma-month to get total market shares and spit that out as market_coverage.csv
				select_products_brandlevel.write_market_coverage(code, area_month_brand, acceptable_brands, largest_brand_left_out)
				## ---------------

				merging_parties = aux.get_parties(info_dict["MergingParties"])

				for timetype in ['month', 'quarter']:
					df = pd.read_csv(base_folder + '/' + folder + '/intermediate/data_' + timetype + '_brandlevel'+'.csv', delimiter = ',')
					df = aux.append_owners_brandlevel(code, df, timetype)
					if timetype == 'month':
						overlap_df = write_overlap(code, df, info_dict["DateCompleted"], merging_parties)
						if "MajorCompetitor" in info_dict:
							major_competitor = aux.get_parties(info_dict["MajorCompetitor"])
							print("Getting major competitor from info.txt")
						else:
							major_competitor = get_major_competitor(overlap_df)
							print("Getting major competitor from shares")
						print(major_competitor)

					dt = datetime.strptime(info_dict["DateCompleted"], '%Y-%m-%d')
					did_brandlevel(df, dt, merging_parties, major_competitor = major_competitor, month_or_quarter = timetype, code = code)

				print("compute_did successfully terminated")
				log_out.close()
				log_err.close()

			except:
				print('brand-level did did not finish successfully')
				log_out.close()
				log_err.close()
				continue

base_folder = '/projects/b1048/gillanes/Mergers/All'
run_all_did_brandlevel(base_folder)