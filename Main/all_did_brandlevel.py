from compute_did_brandlevel import write_overlap, get_major_competitor, did_brandlevel
import os
import sys
import pandas as pd
import auxiliary as aux
from datetime import datetime

def run_all_did_brandlevel(base_folder, month_or_quarter='month'):
	for folder in os.listdir(base_folder):
	# for folder in ['m_1912896020_1']:
		merger_folder = base_folder + '/' + folder + '/output'
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
			print(folder)
			code = folder[2:]

			info_dict = aux.parse_info(code)
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

base_folder = '/projects/b1048/gillanes/Mergers/All'
run_all_did_brandlevel(base_folder)