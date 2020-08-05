import re
import os
import pandas as pd
import auxiliary as aux


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

		#go inside folders with step5 finished
		if (len(folder) > 10 and folder[0] == 'm') and (os.path.exists(merger_folder + '/did_stata_month_0.csv')):

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
				for i in did_merger.columns[1:]:
					aggregated['post_merger_merging'+'_'+i].append(did_merger[i]['post_merger_merging'])


	df = pd.DataFrame.from_dict(aggregated)
	df = df.sort_values(by = 'merger').reset_index().drop('index', axis=1)
	df = aux.clean_betas(df)


	df.to_csv('aggregated.csv', sep = ',')




base_folder = '../../../All/'
get_betas(base_folder)















