# This code samples from the distribution of demographics for each DMA.

import sys
import pandas as pd

# Define function to pull DMA-FIPS crosswalk for each year (from Nielsen stores file)
def pull_dma_shares(year):

        # Import stores data
        stores_path = '../../Data/nielsen_extracts/RMS/'+str(year)+'/Annual_Files/stores_'+str(year)+'.tsv'
        stores_data = pd.read_csv(stores_path, delimiter = '\t',dtype=str)

        # Keep FIPS and DMA information and remove duplicates
        stores_data_sub = stores_data[['year','fips_state_code','fips_county_code','dma_code','dma_descr']]
        stores_data_sub = stores_data_sub.drop_duplicates()

        # Replace county FIPS with relevant zeros
        stores_data_sub['fips_county_code_int'] = stores_data_sub['fips_county_code'].apply(lambda x: '00' + x if len(x)==1 else x)
        stores_data_sub['fips_county_code_full'] = stores_data_sub['fips_county_code_int'].apply(lambda x: '0' + x if len(x)==2 else x)

        # Create full FIPS code and subset to relevant variables
        stores_data_sub['fips'] = stores_data_sub['fips_state_code'] + stores_data_sub['fips_county_code_full']
        stores_data_sub = stores_data_sub[['year','fips','dma_code','dma_descr']]

        # Load PUMA to county mapping
        if year >= 2012:
                pums_xwalk_path = '../../Data/Demographics/county_pums12.csv'
                pums_county_xwalk = pd.read_csv(pums_xwalk_path, delimiter = ',',dtype=str,encoding='latin-1')
                pums_county_xwalk = pums_county_xwalk[['puma12','stab','county','pop10']]
                pums_county_xwalk['pop10'] = pums_county_xwalk['pop10'].astype(int)
                pums_county_xwalk.rename(columns = {'county':'fips','stab':'STATE','puma12':'PUMA'}, inplace = True)
        else:
                pums_xwalk_path = '../../Data/Demographics/county_pums2k.csv'
                pums_county_xwalk = pd.read_csv(pums_xwalk_path, delimiter = ',',dtype=str,encoding='latin-1')
                pums_county_xwalk = pums_county_xwalk[['puma2k','stab','county','pop10']]
                pums_county_xwalk['pop10'] = pums_county_xwalk['pop10'].astype(int)
                pums_county_xwalk.rename(columns = {'county':'fips','stab':'STATE','puma2k':'PUMA'}, inplace = True)

        # Merge PUMA to county mapping
        pums_dma_xwalk = pd.merge(stores_data_sub,pums_county_xwalk,on='fips',how='left')

        # Collapse to DMA/PUMA level
        pums_dma_shares = pums_dma_xwalk.groupby(['dma_code','STATE','PUMA'])['pop10'].agg('sum').reset_index()

        # Create variable to sum population within DMA
        pums_dma_shares['dma_pop'] = pums_dma_shares.groupby('dma_code')['pop10'].transform('sum')
        pums_dma_shares['dma_share'] = pums_dma_shares['pop10']/pums_dma_shares['dma_pop']
        pums_dma_shares = pums_dma_shares[['dma_code','STATE','PUMA','dma_share']]

        # Return dataset with PUMA shares by DMA
        return(pums_dma_shares)

# Define function to sample demographics for a given number of draws
def sample_demographics(year,hhids,pids,ndraw):

        # First, pull PUMA shares by DMA for the given year
        dma_to_puma = pull_dma_shares(year)

        # Next, pull the PUMS person-level data for that year
        pums_path_p = '../../Data/Demographics/pums_' + str(year) + '_p.csv'
        pums_data_p = pd.read_csv(pums_path_p, delimiter = ',',dtype=str)

        # Pull the PUMS household data
        pums_path_hh = '../../Data/Demographics/pums_' + str(year) + '_hh.csv'
        pums_data_hh = pd.read_csv(pums_path_hh, delimiter = ',',dtype=str)

        # Merge people and household data
        pums_data = pd.merge(pums_data_p,pums_data_hh,on=['SERIALNO','PUMA','STATE','YEAR'],how='left')

        # Convert id variables and drop people with any missing value
        pums_data[hhids] = pums_data[hhids].astype('float64')
        pums_data[pids] = pums_data[pids].astype('float64')

        # Restrict to household members 18 years and older. Then, drop NAs.
        pums_data = pums_data[pums_data.AGEP >= 18]
        pums_data = pums_data.dropna()

        # Create variable with number of HH members
        pums_data['person'] = 1
        pums_data['hhmember'] = pums_data.groupby(['SERIALNO','PUMA','STATE','YEAR'])['person'].transform('sum')

        # List of unique DMAs
        dma_unique = dma_to_puma['dma_code'].drop_duplicates()

        # Loop over unique DMAs
        count = 0
        for dd in dma_unique:

                # Counter
                count += 1
                print(dd)

                # Limit PUMA shares to relevant DMA
                puma_shares = dma_to_puma[dma_to_puma['dma_code']==dd]

                # Merge shares onto PUMS data
                pums_data_shares = pd.merge(pums_data,puma_shares,on=['STATE','PUMA'],how='inner')

                # Create counts of observations by PUMA
                pums_data_shares['int'] = 1
                pums_data_shares['obs'] = pums_data_shares.groupby(['STATE','PUMA'])['int'].transform('sum')

                # Sampling probability
                pums_data_shares['sprob'] = pums_data_shares['dma_share']/pums_data_shares['obs']

                # Draw from empirical distribution
                pums_sample_dma = pums_data_shares.sample(n=ndraw[0], replace=True, weights='sprob', random_state=1)
                pums_sample_dma['weight'] = 1/ndraw[0]

                # Append to full dataset
                rel_vars = ['YEAR','dma_code','weight'] + hhids + pids
                if count == 1:
                        demographics_sample = pums_sample_dma[rel_vars]
                else:
                        demographics_sample = demographics_sample.append(pums_sample_dma[rel_vars],ignore_index=True)

        # Export to csv
        out_file = 'Clean/demographics_sample_' + str(year) + '.csv'
        demographics_sample.to_csv (out_file, index = None, header=True)

# Set up inputs and run
if len(sys.argv) != 5:
    print('Error: There must be four arguments.')
    sys.exit()

years_str = sys.argv[1].split(',')
years = [int(yy) for yy in years_str]
hhids = sys.argv[2].split(',')
pids = sys.argv[3].split(',')
ndraw_str = sys.argv[4].split(',')
ndraw = [int(nn) for nn in ndraw_str]

for yr in years:
        sample_demographics(yr,hhids,pids,ndraw)
