import re
import os
import pandas as pd
import auxiliary as aux
import numpy as np

def check_overlap(merger_folder):

	overlap_file = pd.read_csv(merger_folder + '/overlap.csv', sep=',')
	merging_sum = overlap_file['merging_party'].sum()

	if merging_sum < 2:
		return False

	elif merging_sum ==3:
		return True

	elif merging_sum == 2:
		df_merging = overlap_file[overlap_file['merging_party'] == 1]

		if ((df_merging.loc[0,'pre_share'] == 0) & (df_merging.loc[1,'post_share'] == 0)) | ((df_merging.loc[0,'post_share'] == 0) & (df_merging.loc[1,'pre_share'] == 0)):
			return False

		else:
			return True

def get_betas(base_folder):

	#basic specs
	base_folder = '../../../All/'
	aggregated = {}
	aggregated['merger'] = []

	for i in range(45):
		j=i+1
		aggregated['post_merger_merging'+'_'+str(j)] = []

	#loop through folders in "All"
	for folder in os.listdir(base_folder):

		merger_folder = base_folder + folder + '/output'
		no_overlap_ls = []

		#go inside folders with step5 finished
		if (os.path.exists(merger_folder + '/did_stata_month_0.csv')) and check_overlap(merger_folder):

			#overlap_csv = pd.read_csv(base_folder + folder + '/output/overlap.csv')
			#no_overlap_ls = check_overlap(overlap_csv, folder, no_overlap_ls)
			#print(no_overlap_ls)

			did_merger = pd.read_csv(merger_folder + '/did_stata_month_0.csv', sep=',')
			did_merger.index = did_merger['Unnamed: 0']

			#recover only betas for which post_merger_merging exists
			if 'post_merger_merging' in did_merger.index:

				#append the m_folder name to the dictionary
				aggregated['merger'].append(folder)

				#rename col names (just in case someone opened and saved in excel).
				if '(1)' in did_merger.columns:
					for i in did_merger.columns[1:]:
						did_merger.rename(columns={i: i.lstrip('(').rstrip(')')}, inplace=True)
				else:
					for i in did_merger.columns[1:]:
						did_merger.rename(columns={i: i.lstrip('-')}, inplace=True)

					#loop through specs recovering betas
				for i in did_merger.columns[1:46]:
					aggregated['post_merger_merging'+'_'+i].append(did_merger[i]['post_merger_merging'])



	df = pd.DataFrame.from_dict(aggregated)
	df = df.sort_values(by = 'merger').reset_index().drop('index', axis=1)
	df = aux.clean_betas(df)
#	df = df[~df['merger'].isin(no_overlap_ls)]


	df.to_csv('aggregated.csv', sep = ',')




base_folder = '../../../All/'
get_betas(base_folder)




