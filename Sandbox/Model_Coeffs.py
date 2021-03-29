import os
import sys
import pandas as pd
import unicodecsv as csv

def Model_Coeffs(base_folder):

    for folder in os.listdir(base_folder):

        merger_folder = base_folder + folder + '/output'

        if os.path.exists(merger_folder + '/tables'):
            if (len(os.listdir(merger_folder + '/tables')) != 0):

                aggregated = {}
                aggregated['model'] = []
                aggregated['price'] = []
                aggregated['nest']  = []

                for file in os.listdir(merger_folder + '/tables'):

                    read_file = pd.read_csv(merger_folder + '/tables/' + file, sep=",")

                    for col in read_file.columns:
                        read_file[col] = read_file[col].str.replace('="','')
                        read_file[col] = read_file[col].str.replace('*','')
                        read_file[col] = read_file[col].str.replace('"','')

                    aggregated['model'].append(file[2:-4])
                    read_file.set_index('=""')
                    aggregated['price'].append(read_file['="(1)"'][1])
                    aggregated['nest'].append(read_file['="(1)"'][3])

                #print(folder)

                df = pd.DataFrame.from_dict(aggregated)
                df = df.sort_values(by='model').reset_index().drop('index', axis=1)
                df.to_csv(merger_folder + '/' + 'Model_Coeffs.csv', sep=',')

                df = pd.read_csv(merger_folder + '/' + "Model_Coeffs.csv", sep=",")
                df.loc[((df['price']<0) & (df['nest']>0) & (df['nest']<1)), 'Theory'] = 1
                df = df[df['Theory']==1]
                df.to_csv(merger_folder + '/' + "Model_Coeffs.csv")

                if df.shape[0] != 0:
                    print(folder)


log_out = open('output/Model_Coeffs.log', 'w')
log_err = open('output/Model_Coeffs.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
base_folder = '../../../All/'
Model_Coeffs(base_folder)
