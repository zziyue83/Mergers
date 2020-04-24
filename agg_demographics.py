# This script creates aggregate demographics at the DMA level. Specifically, it
# takes the output of sample_demographics.py for a given year and computes
# summary statistics at the DMA level.

import sys
import pandas as pd

def agg_demographics_yr(year):

    # Pull sample_demographics.py dataset
    sample_path = '../../Data/Demographics/demographics_sample_' + str(year) + '.csv'
    sample_data = pd.read_csv(sample_path, delimiter = ',')

    # Compute preliminaries
    # (1) HH income per member
    # (2) Indicator for unemployed
    # (3) Indicator for being in the labor force
    sample_data['hhinc_per_person'] = sample_data['HINCP_ADJ'] / sample_data['hhmember']
    sample_data.loc[sample_data['ESR']==3,'unemployed'] = 1
    sample_data.loc[sample_data['ESR']!=3,'unemployed'] = 0
    sample_data.loc[sample_data['ESR']!=6,'inlaborforce'] = 1
    sample_data.loc[sample_data['ESR']==6,'inlaborforce'] = 0

    # Collapse to the DMA-Year level
    dma_stats = sample_data.groupby(['YEAR','dma_code']).agg({'hhinc_per_person':['mean','median'],
                                                            'unemployed':'sum',
                                                            'inlaborforce':'sum'}).reset_index()
    dma_stats.columns = ['_'.join(col) for col in dma_stats.columns]
    dma_stats.rename(columns = {'YEAR_':'YEAR','dma_code_':'dma_code'}, inplace = True)
    dma_stats['employment_rate'] = 1 - (dma_stats['unemployed_sum']/dma_stats['inlaborforce_sum'])

    # Keep relevant variables
    dma_stats_out = dma_stats[['YEAR','dma_code','hhinc_per_person_mean','hhinc_per_person_median','employment_rate']]
    return(dma_stats_out)

# Loop over years, pull DMA-level demographics, and stack
count = 0
for yr in range(2006,2010):

    # Counter
    count += 1

    # Pull aggregate demographics
    dma_demog = agg_demographics_yr(yr)

    # Append dataset
    if count==1:
        dma_demog_out = dma_demog
    else:
        dma_demog_out = dma_demog_out.append(dma_demog,ignore_index=True)

# Export
dma_demog_out.to_csv('Clean/dma_level_demographics.csv', index = None, header=True)
