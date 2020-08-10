import re
import os
import pandas as pd
import auxiliary as aux
import numpy as np
import sys
import seaborn as sns
sns.set(style='ticks')
colors = ['#838487', '#1b1c1c']
sns.set_palette(sns.color_palette(colors))

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

def get_betas(base_folder, coefficient):

	#basic specs
	base_folder = '../../../All/'
	aggregated = {}
	aggregated['merger'] = []
	aggregated['pre_hhi'] = []
	aggregated['post_hhi'] = []
	aggregated['dhhi'] = []
	coefficient = str(coefficient)

	for i in range(45):

		j=i+1
		aggregated[coefficient+'_'+str(j)] = []

	#loop through folders in "All"
	for folder in os.listdir(base_folder):

		merger_folder = base_folder + folder + '/output'

		#go inside folders with step5 finished
		if (os.path.exists(merger_folder + '/did_stata_month_0.csv')) and check_overlap(merger_folder):

			did_merger = pd.read_csv(merger_folder + '/did_stata_month_0.csv', sep=',')
			did_merger.index = did_merger['Unnamed: 0']

			descr_data = pd.read_csv(merger_folder + '/../intermediate/stata_did_month.csv', sep=',')
			#recover only betas for which post_merger_merging exists
			if coefficient in did_merger.index:

				#append the m_folder name and descriptive stats to the dictionary
				aggregated['merger'].append(folder)
				aggregated['pre_hhi'].append(descr_data.pre_hhi.mean())
				aggregated['post_hhi'].append(descr_data.post_hhi.mean())
				aggregated['dhhi'].append(descr_data.dhhi.mean())

				#rename col names (just in case someone opened and saved in excel).
				if '(1)' in did_merger.columns:

					for i in did_merger.columns[1:]:

						did_merger.rename(columns={i: i.lstrip('(').rstrip(')')}, inplace=True)

				else:

					for i in did_merger.columns[1:]:

						did_merger.rename(columns={i: i.lstrip('-')}, inplace=True)

					#loop through specs recovering betas
				for i in did_merger.columns[1:46]:

					aggregated[coefficient+'_'+i].append(did_merger[i][coefficient])

			#else:
			#	assert coefficient, "Coefficient does not exist: %r" % coefficient

	print(len(aggregated['merger']), len(aggregated['pre_hhi']), len(aggregated['post_hhi']), len(aggregated['dhhi']))


	df = pd.DataFrame.from_dict(aggregated)
	df = df.sort_values(by = 'merger').reset_index().drop('index', axis=1)
	df = aux.clean_betas(df)


	df.to_csv('aggregated.csv', sep = ',')

def basic_plot(specification, coefficient):

	coef = str(coefficient)
	spec = coef+'_'+str(specification)

	fig_name = spec+'.pdf'
	df = pd.read_csv('aggregated.csv', sep=',')
	plot = df.hist(column=spec, color='k', alpha=0.5, bins=10)
	fig = plot[0]
	fig[0].get_figure().savefig('output/'+fig_name)

def scatter_dhhi_plot(specification, coefficient):

	coef = str(coefficient)
	spec = coef+'_'+str(specification)

	fig_name = spec+'dhhi'+'.pdf'
	df = pd.read_csv('aggregated.csv', sep=',')

	#rescaling coefficients for dhhi
	df['dhhi'] = df['dhhi'] * 10000
	plot = sns.regplot(x="dhhi", y=spec, ci = None, data=df,
						scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})

	plot.get_figure().savefig('output/'+fig_name)

def scatter_posthhi_plot(specification, coefficient):

	coef = str(coefficient)
	spec = coef+'_'+str(specification)
	fig_name = spec+'post_hhi'+'.pdf'
	df = pd.read_csv('aggregated.csv', sep=',')
	#rescaling coefficients for dhhi
	df['post_hhi'] = df['post_hhi'] * 10000
	plot = sns.regplot(x="post_hhi", y=spec, ci = None, data=df,
						scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})
	plot.get_figure().savefig('output/'+fig_name)


coef = sys.argv[1]
spec = sys.argv[2]

base_folder = '../../../All/'
get_betas(base_folder, coef)

basic_plot(spec, coef)
scatter_dhhi_plot(spec, coef)
scatter_posthhi_plot(spec, coef)





