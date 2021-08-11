import os
import sys
import pandas as pd
import unicodecsv as csv
import numpy as np

def Model_Coeffs(base_folder):

    '''
    Loops through all folders that successfully completed
    the cross_valid routine. Checks whether the price coeff
    is negative and whether the nesting parameter is in (0,1)
    and recovers those two parameters. It also recovers the
    model number (i.e. xx_zz, where xx stands for the spec
    and zz stands for the nesting scheme).
    '''

    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        if os.path.exists(merger_folder + '/tables'):
            if (len(os.listdir(merger_folder + '/tables')) != 0):

                aggregated = {}
                aggregated['model']    = []
                aggregated['price']    = []
                aggregated['nest']     = []
                aggregated['F-prices'] = []
                aggregated['F-nest']   = []
                aggregated['MSE']      = []

                #print(folder)

                ols_files = []

                for l in range(3):
                    l = l + 1

                    for f in range(6):
                        f = f + 19

                        ols_files.append('r_' + str(f) + '_' + str(l) +'.csv')

                files = [file for file in os.listdir(merger_folder + '/tables') if file not in ols_files]

                for file in files:

                    read_file = pd.read_csv(merger_folder + '/tables/' + file, sep=",")

                    for col in read_file.columns:
                        read_file[col] = read_file[col].str.replace('="','')
                        read_file[col] = read_file[col].str.replace('*','')
                        read_file[col] = read_file[col].str.replace('"','')

                    aggregated['model'].append(file[2:-4])
                    aggregated['price'].append(read_file['="(1)"'][1])
                    aggregated['nest'].append(read_file['="(1)"'][3])

                    read_file = read_file.set_index('=""')
                    aggregated['F-prices'].append(read_file['="(1)"']['F-prices'])
                    aggregated['F-nest'].append(read_file['="(1)"']['F-nest'])
                    aggregated['MSE'].append(read_file['="(1)"']['MSE'])

                for file in ols_files:

                    if os.path.exists(merger_folder + '/tables/' + file):

                        read_file = pd.read_csv(merger_folder + '/tables/' + file, sep=",", skipfooter=1, engine="python")

                        for col in read_file.columns:
                            read_file[col] = read_file[col].str.replace('="','')
                            read_file[col] = read_file[col].str.replace('*','')
                            read_file[col] = read_file[col].str.replace('"','')

                        aggregated['model'].append(file[2:-4])
                        aggregated['price'].append(read_file['="(1)"'][1])
                        aggregated['nest'].append(read_file['="(1)"'][3])

                        read_file = read_file.set_index('=""')
                        aggregated['F-prices'].append(np.nan)
                        aggregated['F-nest'].append(np.nan)
                        aggregated['MSE'].append(read_file['="(1)"']['MSE'])

                df = pd.DataFrame.from_dict(aggregated)
                df = df.sort_values(by='model').reset_index().drop('index', axis=1)
                df.to_csv(merger_folder + '/' + 'Model_Coeffs.csv', sep=',')

                df = pd.read_csv(merger_folder + '/' + "Model_Coeffs.csv", sep=",")
                df.loc[((df['price']<0) & (df['nest']>0) & (df['nest']<1)), 'Theory'] = 1
                df = df[df['Theory']==1]
                df.to_csv(merger_folder + '/' + "Model_Coeffs.csv")


def get_elasticities(base_folder, folder, nest_scheme, nest, price):

    '''
    This function receives the elements that describe a model, and then
    computes the own price elasticities of that model, and returns the
    percentiles of the elasticities distribution on a list ready to be
    incorporated to the final dataset.
    '''

    data_folder = base_folder + folder + '/intermediate'
    df = pd.read_csv(data_folder + '/demand_month.csv', sep=',')

    if nest_scheme == 'inside':
        df['nesting_ids'] = 1

    elif nest_scheme == 'brands':
        if 'brand_code_uc_x' in df.columns:
            df['nesting_ids'] = df['brand_code_uc_x']
        else:
            df['nesting_ids'] = df['brand_code_uc']

    elif nest_scheme == 'prices':
        #get the mean price by brand and split between brands that are above/below
        #the 75-percentile.
        if 'brand_code_uc_x' in df.columns:
            df['mean_price'] = df.groupby('brand_code_uc_x')['prices'].transform('mean')
        else:
            df['mean_price'] = df.groupby('brand_code_uc')['prices'].transform('mean')

        a = np.array(df['mean_price'])
        p75 = np.percentile(a, 75)
        df.loc[df['prices']>=p75, 'nesting_ids'] = 1
        df.loc[df['prices']<p75, 'nesting_ids'] = 0

    # need to compute the within nest shares
    df['nest_shares'] = df.groupby(['market_ids','nesting_ids'])['shares'].transform('sum')
    df['within_nest_shares'] = df['shares']/df['total_nest_shares']

    elasticities = -(price * df['prices'])*(1/(1-nest)-(nest/(1-nest) * df['within_nest_shares'])-df['shares'])
    elasticities = np.array(elasticities)
    elast = []

    for val in range(11):
        p = val * 10
        elast.append(np.nanpercentile(elasticities, p))
    # print(folder)
    print(elast)
    return elast


def Model_Select(base_folder):

    '''
    This function loops through folders in the base_folder,
    enters where the cross_valid routine has been done. Then,
    Recovers the models (indexed by xx_z where xx is the spec
    and z is the nest). Gets the average of the MSE of the
    selected models and returns the selected model based on this.
    '''

    # entries of the dictionary
    models                   = {}
    models['merger']         = []
    models['model_selected'] = []
    models['nest']           = []
    models['price']          = []
    models['F_price']        = []
    models['F_nest']         = []
    models['nesting']        = []
    models['MSE']            = []
    models['Instruments']    = []
    models['Fixed_Effects']  = []
    models['Selected']       = []
    models['model_spec']     = []
    models['nest_scheme']    = []

    for val in range(11):
        p = str(val/10)
        models['elast_'+str(p)] = []

    folder_err = ['m_1817013020_2']
    folders = [folder for folder in os.listdir(base_folder) if folder not in folder_err]

    #lists of the elements that describe a model
    nests = ['inside', 'brands', 'prices']
    Fixed_Effects = ['upc', 'upc_dma', 'upc_dma_cal', 'upc_dma_per', 'upc_cal', 'upc_per']
    Instruments = ['cost_Nupc', 'dist_dies_tot_cost', 'dist_dies_tot_cost_Nupc', 'OLS']

    for folder in folders:

        coeff_folder  = base_folder + folder + '/output'
        demand_folder = base_folder + folder + '/intermediate'

        if (os.path.exists(coeff_folder + '/Model_Coeffs.csv') and
           os.path.exists(demand_folder + '/demand_month.csv')):

            # print(folder)
            df = pd.read_csv(coeff_folder + '/Model_Coeffs.csv', delimiter=",")

            # print(df.head())
            if df.shape[0] != 0:

                # for each model that satisfies theory restrictions we recover
                # the elements that describe a model and fill the dictionary.
                for i in range(df.shape[0]):

                    idxmin = df['MSE'].idxmin()
                    models['merger'].append(folder)
                    models['model_selected'].append(df['model'][i])
                    models['nest'].append(df['nest'][i])
                    nest  = df['nest'][i]
                    models['price'].append(df['price'][i])
                    price = df['price'][i]
                    models['F_price'].append(df['F-prices'][i])
                    models['F_nest'].append(df['F-nest'][i])
                    models['nest_scheme'].append(int(df['model'][i].split('_')[1]))
                    models['model_spec'].append(int(df['model'][i].split('_')[0]))
                    models['nesting'].append(nests[int(df['model'][i].split('_')[1])-1])
                    nest_scheme = nests[int(df['model'][i].split('_')[1])-1]
                    models['MSE'].append(df['MSE'][i])

                    inst = int(np.ceil(int(df['model'][i].split('_')[0])/6)-1)
                    f_e  = int(int(df['model'][i].split('_')[1])%6-1)

                    models['Instruments'].append(Instruments[inst])
                    models['Fixed_Effects'].append(Fixed_Effects[f_e])

                    print(folder)
                    print(nest_scheme)
                    print(nest)
                    print(price)
                    elast = get_elasticities(base_folder, folder, nest_scheme,
                                             nest, price)

                    for val in range(11):
                        p = val/10
                        models['elast_'+str(p)].append(elast[val])

                    if idxmin == i:

                        models['Selected'].append(1)

                    else:

                        models['Selected'].append(0)

            else:

                # if no model is selected by theory we fill with empty values.
                models['merger'].append(folder)
                models['model_selected'].append(np.nan)
                models['nest'].append(np.nan)
                models['price'].append(np.nan)
                models['F_price'].append(np.nan)
                models['F_nest'].append(np.nan)
                models['MSE'].append(np.nan)
                models['nesting'].append(np.nan)
                models['nest_scheme'].append(np.nan)
                models['model_spec'].append(np.nan)

                models['Instruments'].append(np.nan)
                models['Fixed_Effects'].append(np.nan)
                models['Selected'].append(np.nan)

                for val in range(11):
                    p = val/10
                    models['elast_'+str(p)].append(np.nan)

    # get a dataset from the dictionary.
    df = pd.DataFrame.from_dict(models)
    df = df.sort_values(by=['merger', 'model_spec', 'nest_scheme']).reset_index().drop('index', axis=1)
    df = df.dropna(axis=1, how='all')
    df.to_csv('output/Models.csv', sep=',')


log_out = open('output/Model_Coeffs.log', 'w')
log_err = open('output/Model_Coeffs.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'
Model_Coeffs(base_folder)
Model_Select(base_folder)
