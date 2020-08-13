
#import matplotlib
#matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import re
import os
import pandas as pd
import auxiliary as aux
import numpy as np
import sys
import statsmodels.api as sm
from statsmodels.iolib.summary2 import summary_col
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


def get_betas(base_folder):

	#basic specs
	base_folder = '../../../All/'
	aggregated = {}
	aggregated['merger'] = []
	aggregated['pre_hhi'] = []
	aggregated['post_hhi'] = []
	aggregated['dhhi'] = []
	#coefficient = str(coefficient)

	for i in range(45):

		j=i+1
		aggregated['post_merger'+'_'+str(j)] = []
		aggregated['se_pm_'+str(j)] = []
		aggregated['pval_pm_'+str(j)] = []

		aggregated['post_merger_merging_'+str(j)] = []
		aggregated['se_pmm_'+str(j)] = []
		aggregated['pval_pmm_'+str(j)] = []

	#loop through folders in "All"
	for folder in os.listdir(base_folder):

		merger_folder = base_folder + folder + '/output'

		#go inside folders with step5 finished
		if (os.path.exists(merger_folder + '/did_stata_month_0.csv')) and check_overlap(merger_folder):

			did_merger = pd.read_csv(merger_folder + '/did_stata_month_0.csv', sep=',')
			did_merger.index = did_merger['Unnamed: 0']

			descr_data = pd.read_csv(merger_folder + '/../intermediate/stata_did_month.csv', sep=',')
			#recover only betas for which post_merger_merging exists
			if 'post_merger_merging' and 'post_merger' in did_merger.index:

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

					aggregated['post_merger_merging'+'_'+i].append(did_merger[i]['post_merger_merging'])
					aggregated['se_pmm_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger_merging')+1)])
					aggregated['pval_pmm_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger_merging')+2)])

					aggregated['post_merger'+'_'+i].append(did_merger[i]['post_merger'])
					aggregated['se_pm_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger')+1)])
					aggregated['pval_pm_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger')+2)])

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

	fig_name = 'pmm_'+str(specification)+'.pdf'
	df = pd.read_csv('aggregated.csv', sep=',')
	plot = df.hist(column=spec, color='k', alpha=0.5, bins=10)
	fig = plot[0]
	fig[0].get_figure().savefig('output/'+fig_name)


def basic_plot2(specification):

	#coef = str(coefficient)
	spec = str(specification)
	fig_name = 'pmm_pm_'+spec+'.pdf'
	df = pd.read_csv('aggregated.csv', sep=',')
	df['total_post_'+spec] = df['post_merger_'+spec]+df['post_merger_merging_'+spec]
	plot = df.hist(column='total_post_'+spec, color='k', alpha=0.5, bins=10)
	fig = plot[0]
	fig[0].get_figure().savefig('output/'+fig_name)


def scatter_dhhi_plot(specification, coefficient):

	coef = str(coefficient)
	spec = coef+'_'+str(specification)

	fig_name = 'dhhi2'+'.pdf'
	df = pd.read_csv('aggregated.csv', sep=',')

	#rescaling coefficients for dhhi
	df['dhhi'] = df['dhhi'] * 10000
	min_y = df[spec].min()-df[spec].std()
	max_y = df[spec].max()+df[spec].std()
	plot1 = sns.regplot(x="dhhi", y=spec, ci = None, data=df,
						scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})
	plot1.set(ylim=(min_y, max_y))

	#plot.set(xlim=(df['dhhi'].min(), df['dhhi'].max()))
	plot1.get_figure().savefig('output/'+fig_name)
	plt.clf()


def scatter_posthhi_plot(specification, coefficient):

	coef = str(coefficient)
	spec = coef+'_'+str(specification)

	fig_name = 'post_hhi'+'.pdf'
	df = pd.read_csv('aggregated.csv', sep=',')

	#rescaling coefficients for dhhi
	df['post_hhi'] = df['post_hhi'] * 10000
	min_y = df[spec].min()-df[spec].std()
	max_y = df[spec].max()+df[spec].std()
	plot2 = sns.regplot(x="post_hhi", y=spec, ci = None, data=df,
						scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})
	#plot.set(xlim=(df['post_hhi'].min(), df['post_hhi'].max()))

	plot2.set(ylim=(min_y, max_y))
	plot2.get_figure().savefig('output/'+fig_name)
	plt.clf()


def reg_table1(specification, coefficient):

	spec = str(specification)
	df = pd.read_csv('aggregated.csv', sep=',')

	df['post_hhi'] = df['post_hhi']
	df['dhhi'] = df['dhhi']

	Y1 = df[['post_merger_merging_' + spec]]
	X1 = df[['post_hhi', 'dhhi']]
	X1 = sm.add_constant(X1)

	df['dhhi2'] = df['dhhi']**2
	df['post_hhi2'] = df['post_hhi']**2
	df['dhhi_posthhi'] = df['dhhi']*df['post_hhi']

	X2 = df[['post_hhi', 'dhhi', 'dhhi_posthhi', 'post_hhi2', 'dhhi2']]
	X2 = sm.add_constant(X2)

	model1 = sm.WLS(Y1, X1, weights=df['se_pmm_' + spec]).fit(cov_type='HC1')
	model2 = sm.WLS(Y1, X2, weights=df['se_pmm_' + spec]).fit(cov_type='HC1')

	table1 = summary_col (results = [model1,model2],stars=True,float_format='%0.3f',
						model_names = ['(1)\npmm','(2)\npmm'],
						regressor_order = ['post_hhi', 'dhhi','dhhi_posthhi','post_hhi2','dhhi2','const'],
						info_dict={'N':lambda x: "{0:d}".format(int(x.nobs))})
	print(table1)


coef = sys.argv[1]
spec = sys.argv[2]
base_folder = '../../../All/'

log_out = open('output/aggregation.log', 'w')
log_err = open('output/aggregation.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

get_betas(base_folder)

basic_plot(spec, coefficient='post_merger_merging')
basic_plot2(spec)
scatter_dhhi_plot(spec, coef)
scatter_posthhi_plot(spec, coef)
reg_table1(spec, coef)






