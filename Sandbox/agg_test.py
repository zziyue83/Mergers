
#import matplotlib
# matplotlib.use("TkAgg")
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
import array_to_latex as a2l

sns.set(style='ticks')
colors = ['#838487', '#1b1c1c']
sns.set_palette(sns.color_palette(colors))


def check_overlap(merger_folder):

    overlap_file = pd.read_csv(merger_folder + '/overlap.csv', sep=',')
    merging_sum = overlap_file['merging_party'].sum()
    c4 = overlap_file['pre_share'].nlargest(4).sum()

    if merging_sum < 2:
        return (False, c4)

    elif merging_sum == 3:
        return (True, c4)

    elif merging_sum == 2:

        df_merging = overlap_file[overlap_file['merging_party'] == 1]

        if ((df_merging.loc[0, 'pre_share'] == 0) & (df_merging.loc[1, 'post_share'] == 0)) | ((df_merging.loc[0, 'post_share'] == 0) & (df_merging.loc[1, 'pre_share'] == 0)):
            return (False, c4)

        else:
            return (True, c4)


def get_betas(base_folder):

    # basic specs
    base_folder = '../../../All/'
    aggregated = {}
    aggregated['merger'] = []
    aggregated['pre_hhi'] = []
    aggregated['post_hhi'] = []
    aggregated['dhhi'] = []
    aggregated['c4'] = []
    #coefficient = str(coefficient)

    for i in range(45):

        j = i+1
        aggregated['post_merger'+'_'+str(j)] = []
        aggregated['se_pm_'+str(j)] = []
        aggregated['pval_pm_'+str(j)] = []

        aggregated['post_merger_dhhi_'+str(j)] = []
        aggregated['se_pmmd_'+str(j)] = []
        aggregated['pval_pmmd_'+str(j)] = []

    # loop through folders in "All"
    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        # go inside folders with step5 finished
        if (os.path.exists(merger_folder + '/did_stata_month_2.csv')) and check_overlap(merger_folder)[0]:

            did_merger = pd.read_csv(merger_folder + '/did_stata_month_2.csv', sep=',')
            did_merger.index = did_merger['Unnamed: 0']

            descr_data = pd.read_csv(
                merger_folder + '/../intermediate/stata_did_month.csv', sep=',')
            # recover only betas for which post_merger_merging exists
            if 'post_merger_dhhi' in did_merger.index:

                # append the m_folder name and descriptive stats to the dictionary
                aggregated['merger'].append(folder)
                aggregated['c4'].append(check_overlap(merger_folder)[1])
                aggregated['pre_hhi'].append(descr_data.pre_hhi.mean())
                aggregated['post_hhi'].append(descr_data.post_hhi.mean())
                aggregated['dhhi'].append(descr_data.dhhi.mean())

                # rename col names (just in case someone opened and saved in excel).
                if '(1)' in did_merger.columns:

                    for i in did_merger.columns[1:]:

                        did_merger.rename(
                            columns={i: i.lstrip('(').rstrip(')')}, inplace=True)

                else:

                    for i in did_merger.columns[1:]:

                        did_merger.rename(
                            columns={i: i.lstrip('-')}, inplace=True)

                    # loop through specs recovering betas
                for i in did_merger.columns[1:46]:

                    aggregated['post_merger_dhhi'+'_'+i].append(did_merger[i]['post_merger_dhhi'])
                    aggregated['se_pmmd_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger_dhhi')+1)])
                    aggregated['pval_pmmd_'+i].append(did_merger[i][(did_merger.index.get_loc('post_merger_dhhi')+2)])

                    aggregated['post_merger'+'_' +
                               i].append(did_merger[i]['post_merger'])
                    aggregated['se_pm_'+i].append(did_merger[i]
                                                  [(did_merger.index.get_loc('post_merger')+1)])
                    aggregated['pval_pm_'+i].append(did_merger[i]
                                                    [(did_merger.index.get_loc('post_merger')+2)])

            # else:
            #	assert coefficient, "Coefficient does not exist: %r" % coefficient

    print(len(aggregated['merger']), len(aggregated['pre_hhi']), len(
        aggregated['post_hhi']), len(aggregated['dhhi']))

    df = pd.DataFrame.from_dict(aggregated)
    df = df.sort_values(by='merger').reset_index().drop('index', axis=1)
#    df = aux.clean_betas(df)

    df.to_csv('aggregated.csv', sep=',')

# pmm hist


# def basic_plot(specification, coefficient):

#     coef = str(coefficient)
#     spec = coef+'_'+str(specification)

#     fig_name = 'pm_dhhi_'+str(specification)+'.pdf'
#     df = pd.read_csv('aggregated.csv', sep=',')
#     plot = df.hist(column=spec, color='k', alpha=0.5, bins=10)
#     fig = plot[0]
#     fig[0].get_figure().savefig('output/'+fig_name)

# # pmm+pm hist


# def basic_plot2(specification):

#     #coef = str(coefficient)
#     spec = str(specification)
#     fig_name = 'pmd_pm_'+spec+'.pdf'
#     df = pd.read_csv('aggregated.csv', sep=',')
#     df['total_post_'+spec] = df['post_merger_'+spec] + df['post_merger_dhhi_'+spec]
#     plot = df.hist(column='total_post_'+spec, color='k', alpha=0.5, bins=10)
#     fig = plot[0]
#     fig[0].get_figure().savefig('output/'+fig_name)

# dhhi vs pmm


# def scatter_dhhi_plot(specification, coefficient):

#     coef = str(coefficient)
#     spec = coef+'_'+str(specification)

#     fig_name = 'dhhi2'+'.pdf'
#     df = pd.read_csv('aggregated.csv', sep=',')

#     # rescaling coefficients for dhhi
#     df['dhhi'] = df['dhhi'] * 10000
#     min_y = df[spec].min()-df[spec].std()
#     max_y = df[spec].max()+df[spec].std()
#     plot1 = sns.regplot(x="dhhi", y=spec, ci=None, data=df,
#                         scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})
#     plot1.set(ylim=(min_y, max_y))

#     #plot.set(xlim=(df['dhhi'].min(), df['dhhi'].max()))
#     plot1.get_figure().savefig('output/'+fig_name)
#     plt.clf()

# # post_hhi vs pmm


# def scatter_posthhi_plot(specification, coefficient):

#     coef = str(coefficient)
#     spec = coef+'_'+str(specification)

#     fig_name = 'post_hhi'+'.pdf'
#     df = pd.read_csv('aggregated.csv', sep=',')

#     # rescaling coefficients for dhhi
#     df['post_hhi'] = df['post_hhi'] * 10000
#     min_y = df[spec].min()-df[spec].std()
#     max_y = df[spec].max()+df[spec].std()

#     plot2 = sns.regplot(x="post_hhi", y=spec, ci=None, data=df,
#                         scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})

#     #plot.set(xlim=(df['post_hhi'].min(), df['post_hhi'].max()))

#     plot2.set(ylim=(min_y, max_y))
#     plot2.get_figure().savefig('output/'+fig_name)
#     plt.clf()

# # C4 vs pmm+pm and C4 vs pmm


# def scatter_c4_plot(specification, coefficient):

#     coef = str(coefficient)
#     spec = str(specification)

#     fig_name = 'c4_tot'+'.pdf'
#     df = pd.read_csv('aggregated.csv', sep=',')
#     df['total_post_'+spec] = df['post_merger_'+spec] + \
#         df['post_merger_merging_'+spec]

#     # rescaling coefficients for dhhi
#     min_y = df['total_post_'+spec].min()-df['total_post_'+spec].std()
#     max_y = df['total_post_'+spec].max()+df['total_post_'+spec].std()

#     plot2 = sns.regplot(x="c4", y='total_post_'+spec, ci=None, data=df,
#                         scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})
#     plot2.set(xlabel='C4', ylabel='pmm+pm')
#     #plot.set(xlim=(df['post_hhi'].min(), df['post_hhi'].max()))

#     plot2.set(ylim=(min_y, max_y))
#     plot2.get_figure().savefig('output/'+fig_name)
#     plt.clf()

#     fig_name1 = 'c4_pmm'+'.pdf'
#     min_y = df['post_merger_merging_'+spec].min() - \
#         df['post_merger_merging_'+spec].std()
#     max_y = df['post_merger_merging_'+spec].max() + \
#         df['post_merger_merging_'+spec].std()

#     plot3 = sns.regplot(x="c4", y='post_merger_merging_'+spec, ci=None, data=df,
#                         scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})
#     plot3.set(xlabel='C4', ylabel='pmm')
#     #plot.set(xlim=(df['post_hhi'].min(), df['post_hhi'].max()))

#     plot3.set(ylim=(min_y, max_y))
#     plot3.get_figure().savefig('output/'+fig_name1)
#     plt.clf()

# # pm vs pmm


# def scatter_merging_plot(specification):

#     spec = str(specification)
#     fig_name = 'merge_non_merging'+'.pdf'
#     df = pd.read_csv('aggregated.csv', sep=',')

#     # rescaling coefficients for dhhi
#     min_y = df['post_merger_'+spec].min()-df['post_merger_'+spec].std()
#     max_y = df['post_merger_'+spec].max()+df['post_merger_'+spec].std()

#     plot3 = sns.regplot(x='post_merger_merging_'+spec, y='post_merger_'+spec, ci=None, data=df,
#                         scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})

#     #plot.set(xlim=(df['post_hhi'].min(), df['post_hhi'].max()))

#     plot3.set(ylim=(min_y, max_y))
#     plot3.get_figure().savefig('output/'+fig_name)
#     plt.clf()

#     df['total_post_'+spec] = df['post_merger_'+spec] + \
#         df['post_merger_merging_'+spec]
#     plot4 = sns.regplot(x='total_post_'+spec, y='post_merger_'+spec, ci=None, data=df,
#                         scatter_kws={"color": colors[0]}, line_kws={"color": colors[1]})

#     min_y2 = df['total_post_'+spec].min()-df['total_post_'+spec].std()
#     max_y2 = df['total_post_'+spec].max()+df['total_post_'+spec].std()
#     fig_name2 = 'merge_non_merging_total'+'.pdf'

#     plot3.set(ylim=(min_y2, max_y2))
#     plot3.get_figure().savefig('output/'+fig_name2)
#     plt.clf()

# # pm vs pmm


# def dhhi_posthhi(specification):

#     spec = str(specification)
#     fig_name = 'dhhi_post_hhi'+'.pdf'
#     df = pd.read_csv('aggregated.csv', sep=',')

#     # rescaling coefficients for dhhi
#     df['post_hhi'] = df['post_hhi'] * 10000
#     df['dhhi'] = df['dhhi'] * 10000

#     min_y = df['dhhi'].min()-df['dhhi'].std()
#     max_y = df['dhhi'].max()+df['dhhi'].std()

#     df.loc[(df['post_merger_merging_'+spec] > 0), 'Size'] = 1
#     df.loc[(df['post_merger_merging_'+spec] <= 0), 'Size'] = 0

#     plot3 = sns.scatterplot(x='post_hhi', y='dhhi',
#                             data=df, hue='Size', legend='full', palette=[colors[0], colors[1]])

#     plot3.set(ylim=(min_y, max_y))
#     plot3.legend(title='pmm sign', loc='upper right', labels=['b>0', 'b<=0'])
#     plot3.get_figure().savefig('output/'+fig_name)
#     plt.clf()

# # regs


# def reg_table1(specification, coefficient):

#     spec = str(specification)
#     df = pd.read_csv('aggregated.csv', sep=',')

#     df['post_hhi'] = df['post_hhi']
#     df['dhhi'] = df['dhhi']

#     Y1 = df[['post_merger_merging_' + spec]]
#     X1 = df[['post_hhi', 'dhhi']]
#     X1 = sm.add_constant(X1)

#     df['dhhi2'] = df['dhhi']**2
#     df['post_hhi2'] = df['post_hhi']**2
#     df['dhhi_posthhi'] = df['dhhi']*df['post_hhi']

#     X2 = df[['post_hhi', 'dhhi', 'dhhi_posthhi', 'post_hhi2', 'dhhi2']]
#     X2 = sm.add_constant(X2)

#     X3 = df[['post_hhi', 'dhhi', 'c4']]
#     X3 = sm.add_constant(X3)

#     Y2 = df['post_merger_'+spec]+df['post_merger_merging_'+spec]

#     weights = 1/df['se_pmm_'+spec]

#     model1 = sm.WLS(Y1, X1, weights=weights).fit(cov_type='HC1')
#     model2 = sm.WLS(Y1, X2, weights=weights).fit(cov_type='HC1')
#     model3 = sm.WLS(Y1, X3, weights=weights).fit(cov_type='HC1')
#     model4 = sm.OLS(Y1, X1).fit(cov_type='HC1')
#     model5 = sm.OLS(Y1, X2).fit(cov_type='HC1')
#     model6 = sm.OLS(Y1, X3).fit(cov_type='HC1')
#     model7 = sm.WLS(Y2, X1, weights=weights).fit(cov_type='HC1')
#     model8 = sm.WLS(Y2, X2, weights=weights).fit(cov_type='HC1')
#     model9 = sm.WLS(Y2, X3, weights=weights).fit(cov_type='HC1')

#     table1 = summary_col(results=[model1, model2, model3], stars=True, float_format='%0.3f',
#                          model_names=['(1)\npmm', '(2)\npmm', '(3)\npmm'],
#                          regressor_order=[
#                              'post_hhi', 'dhhi', 'dhhi_posthhi', 'post_hhi2', 'dhhi2', 'c4', 'const'],
#                          info_dict={'N': lambda x: "{0:d}".format(int(x.nobs))})

#     table2 = summary_col(results=[model4, model5, model6], stars=True, float_format='%0.3f',
#                          model_names=['(1)\npmm', '(2)\npmm', '(3)\npmm'],
#                          regressor_order=[
#                              'post_hhi', 'dhhi', 'dhhi_posthhi', 'post_hhi2', 'dhhi2', 'c4', 'const'],
#                          info_dict={'N': lambda x: "{0:d}".format(int(x.nobs))})

#     table3 = summary_col(results=[model7, model8, model9], stars=True, float_format='%0.3f',
#                          model_names=[
#         '(1)\npmm+pm', '(2)\npmm+pm', '(3)\npmm+pm'],
#         regressor_order=[
#                              'post_hhi', 'dhhi', 'dhhi_posthhi', 'post_hhi2', 'dhhi2', 'c4', 'const'],
#         info_dict={'N': lambda x: "{0:d}".format(int(x.nobs))})

#     print(table1.as_latex())
#     print(table2.as_latex())
#     print(table3.as_latex())


coef = sys.argv[1]
spec = sys.argv[2]
base_folder = '../../../All/'

log_out = open('output/aggregation.log', 'w')
log_err = open('output/aggregation.err', 'w')
sys.stdout = log_out
sys.stderr = log_err

get_betas(base_folder)

basic_plot(spec, coefficient='post_merger_dhhi')
basic_plot2(spec)
# scatter_dhhi_plot(spec, coef)
# scatter_posthhi_plot(spec, coef)
# scatter_merging_plot(spec)
# scatter_c4_plot(spec, coef)
# dhhi_posthhi(spec)
# reg_table1(spec, coef)
