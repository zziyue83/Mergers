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

	elif code == '2735179020_20':
		# These are typos in sizes and units of hair accesories
		df.loc[(df.multi * df.size1_amount == 4.6) & (df.size1_units == 'OZ'), 'size1_amount'] = 4
		df.loc[(df.multi * df.size1_amount == 0.005) & (df.size1_units == 'OZ'), 'size1_amount'] = 5
		df.loc[df.size1_units == 'OZ', 'size1_units'] = 'CT'

	elif code == '3035705020_5':
		# These are small data isses on eye shadows
		df.loc[(df.multi * df.size1_amount == 32) & (df.size1_units == 'OZ'), 'size1_amount'] = 0.32

	elif code == '3035705020_7':
		# These are small data isses on lip remedies
		df.loc[(df.size1_amount == 15) & (df.multi == 1 )& (df.size1_units == 'OZ'), 'size1_amount'] = 0.15
		df.loc[(df.size1_amount == 25) & (df.multi == 1 )& (df.size1_units == 'OZ'), 'size1_amount'] = 0.25
		df.loc[(df.size1_amount == 35) & (df.multi == 1 )& (df.size1_units == 'OZ'), 'size1_amount'] = 0.35
		df.loc[(df.size1_amount == 150) & (df.multi == 1 )& (df.size1_units == 'OZ'), 'size1_amount'] = 0.15


	return df
