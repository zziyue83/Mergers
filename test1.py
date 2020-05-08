import pandas as pd
#df = pd.read_csv('CANDY_GUM_quarter_pre_model_with_distance.tsv', delimiter = '\t')
df1 = pd.read_csv('../../GeneratedData/BEER_pre_model_quarter_with_distance.tsv', delimiter = '\t')
df2 = pd.read_csv('../../GeneratedData/BEER_pre_model_quarter_data.tsv', delimiter = '\t')
df3 = pd.read_csv('../../GeneratedData/BEER_quarter_pre_model_with_distance.tsv', delimiter = '\t')
print(df1.equals(df3))
print(len(df2))
print(len(df1))
print(len(df3))
