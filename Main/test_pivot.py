import pandas as pd
import numpy as np

df = pd.read_csv('../../../All/m_1973045020_1/output/536746_unstacked_error.csv')
df = df.groupby(['upc','store-week'], as_index = False).agg({'price':'first'})
df = df.pivot_table(index = 'store-week', columns = 'upc', values = 'price', aggfunc = 'first')
print(df.head())

import numpy as np
import pandas as pd
df = pd.read_csv('../../../All/m_1912896020_1/properties/characteristics.csv')
#df['imported'] = np.where(df['style_descr'] == 'IMPORTED', 1, 0)
df['type'] = np.where((df['brand_descr'].str.contains('LIGHT')) | (df['brand_descr'].str.contains('LITE')), 'LIGHT', 0)
df.loc[df['formula_descr'] == 'REGULAR', 'type'] = 'REGULAR'
df.loc[df['brand_descr'].str.contains(' NA '), 'type'] = 'NON-ALCOHOLIC'
df.to_csv('../../../All/m_1912896020_1/properties/characteristics.csv', sep = ',', index = False)