# This script pulls ACS 5-year estimates at the county level for periods ending
# in specified years. Then, it merges on the mapping to Nielsen DMAs and
# aggregates to the DMA level.

import sys
import pandas as pd
import censusdata

# Define function to load county-level datasets for all years and stack
def pull_demographics(years,weight,ids):

    # Loop over years, pull county-level data, and stack
    count = 0
    for yr in years:

        # Counter
        count+=1

        # Import Census data for given year
        full_ids = weight + ids
        census_import = censusdata.download('acs5', yr, censusdata.censusgeo([('county', '*')]),full_ids)
        census_import['year'] = yr

        # Format FIPS code
        fips_full_list = list(censusdata.geographies(censusdata.censusgeo([('county', '*')]), 'acs5', yr).values())
        fips_list = [ii.params() for ii in fips_full_list]
        state_fips = [ii[0][1] for ii in fips_list]
        census_import['fips_state_code'] = [int(ss) for ss in state_fips]
        cty_fips = [ii[1][1] for ii in fips_list]
        census_import['fips_county_code'] = [int(cc) for cc in cty_fips]

        # Append to full dataset
        if count == 1:
            demog_all_years = census_import
        else:
            demog_all_years = demog_all_years.append(census_import,ignore_index=True)

    # Set final county-level dataset
    rel_vars = ['year','fips_state_code','fips_county_code'] + full_ids
    demog_all_years_vars = demog_all_years[rel_vars]

    # Return final dataset
    return(demog_all_years_vars)

# Define function to pull DMA-FIPS crosswalk for each year (from Nielsen stores file)
def pull_dma_xwalk(years):

    # Loop over years, pull DMA to county mapping from stores file for each year
    count = 0
    for yr in years:

        # Counter
        count+=1

        # Import stores data
        stores_path = '../../Data/nielsen_extracts/RMS/'+str(yr)+'/Annual_Files/stores_'+str(yr)+'.tsv'
        stores_data = pd.read_csv(stores_path, delimiter = '\t')

        # Keep FIPS and DMA information and remove duplicates
        stores_data_sub = stores_data[['year','fips_state_code','fips_county_code','dma_code','dma_descr']]
        stores_data_stack = stores_data_sub[['year','fips_state_code','fips_county_code','dma_code','dma_descr']]
        stores_data_stack = stores_data_stack.drop_duplicates()

        # Append to full dataset
        if count == 1:
            dma_all_years = stores_data_stack
        else:
            dma_all_years = dma_all_years.append(stores_data_stack,ignore_index=True)

    # Return full dataset
    return(dma_all_years)

# Define function to aggregate demographics to the DMA level
def aggregate_demographics(years,weight,ids):

    # Pull demographic dataset
    demographics = pull_demographics(years,weight,ids)

    # Pull DMA crosswalk
    dma_counties = pull_dma_xwalk(years)

    # Merge demographics onto DMA/county dataset
    dma_counties_demog = pd.merge(dma_counties,demographics,on=['year','fips_state_code','fips_county_code'],how='left')

    # Create weighted variables
    wt_vars = []
    for cc in ids:
        new_var = cc + '_wt'
        dma_counties_demog[new_var] = dma_counties_demog[cc]*dma_counties_demog[weight[0]]
        wt_vars.append(new_var)

    # Aggregate to DMA level (weighted averages of weight variable)
    agg_vars = weight + wt_vars
    dma_demographics = dma_counties_demog.groupby(['year','dma_code'])[agg_vars].agg('sum').reset_index()

    # Compute weighted averages
    avg_vars = []
    for cc in ids:
        wt_var_name = cc + '_wt'
        avg_var_name = cc + '_avg'
        dma_demographics[avg_var_name] = dma_demographics[wt_var_name]/dma_demographics[weight[0]]
        avg_vars.append(avg_var_name)

    # Restrict to relevant variables
    rel_vars_demog = ['year','dma_code'] + weight + avg_vars
    dma_demographics = dma_demographics[rel_vars_demog]

    # Export to csv
    dma_demographics.to_csv ('Clean/dma_demographics.csv', index = None, header=True)

# Set up inputs and run
if len(sys.argv) != 4:
    print('Error: There must be three arguments.')
    sys.exit()

years_str = sys.argv[1].split(',')
years = [int(yy) for yy in years_str]
weight = sys.argv[2].split(',')
ids = sys.argv[3].split(',')

aggregate_demographics(years,weight,ids)
