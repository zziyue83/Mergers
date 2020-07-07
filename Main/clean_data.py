import pandas as pd
import numpy as np

def clean_data(code, df):
	if code == '2600981020_1':
		# Large sizes of liquor should be in ML, not OZ
		df.loc[(df.multi * df.size1_amount == 1986) & (df.size1_units == 'OZ'), 'size1_units'] = 'ML'
		df.loc[(df.multi * df.size1_amount == 2130) & (df.size1_units == 'OZ'), 'size1_units'] = 'ML'

	elif code == '1973045020_1':
		# These are small Pez dispensers
		df.loc[(df.multi * df.size1_amount == 87) & (df.size1_units == 'OZ'), 'size1_amount'] = .87


	elif code == '2614332020_1':
		# These should be counts of cigarettes
		df.loc[(df.multi * df.size1_amount == 200) & (df.size1_units == 'OZ'), 'size1_units'] = 'CT'	

	elif code == '2736521020_1':
		# These are pickle-in-a-pouch-type things (not comparable to 1 jar)
		df.loc[df.size1_units == 'CT', 'size1_amount'] = df.size1_amount[df.size1_units == 'CT'] * 3.75
		df.loc[df.size1_units == 'CT', 'size1_units'] = 'OZ'

	elif code == '2735179020_11':
		# This is a typo on eyeliner
		df.loc[(df.multi * df.size1_amount == 39) & (df.size1_units == 'OZ'), 'size1_amount'] = 0.039

	return df
