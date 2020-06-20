import pandas as pd
import numpy as np

def clean_data(code, df):
	if code == '2600981020_1':
		df.loc[(df.multi * df.size1_amount == 1986) & (df.size1_units == 'OZ'), 'size1_units'] = 'ML'
		df.loc[(df.multi * df.size1_amount == 2130) & (df.size1_units == 'OZ'), 'size1_units'] = 'ML'

	if code == '1973045020_1':
		df.loc[(df.multi * df.size1_amount == 87) & (df.size1_units == 'OZ'), 'size1_amount'] = .87

	return df
