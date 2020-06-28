# This code samples from the distribution of demographics for each DMA.

import sys
import pandas as pd
import pyblp

# Define function to pull DMA-FIPS crosswalk for each year (from Nielsen stores file)
def pull_dma_shares(year):

        # Import stores data
        stores_path = '../../Data/nielsen_extracts/RMS/'+str(year)+'/Annual_Files/stores_'+str(year)+'.tsv'
        stores_data = pd.read_csv(stores_path, delimiter = '\t',dtype=str)

        # Keep FIPS and DMA information and remove duplicates
        stores_data_sub = stores_data[['year','fips_state_code','fips_county_code','dma_code','dma_descr']]
        stores_data_sub.fips_state_code = stores_data_sub.fips_state_code.fillna(value='')
        stores_data_sub.fips_county_code = stores_data_sub.fips_county_code.fillna(value='')
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

def import_pums(year,hhids,pids):

        # Set path and import person data
        pums_path_p = '../../Data/Demographics/pums_' + str(year) + '_p.csv'
        pums_data_p = pd.read_csv(pums_path_p, delimiter = ',',dtype=str)

        # Set path and import household data
        pums_path_hh = '../../Data/Demographics/pums_' + str(year) + '_hh.csv'
        pums_data_hh = pd.read_csv(pums_path_hh, delimiter = ',',dtype=str)

        # Merge person and household data
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
        return(pums_data)

# Define function to sample demographics for a given year, dma, and number of draws
def sample_demographics(year,dma,hhids,pids,ndraw,dma_to_puma,pums_data):

        # Limit PUMA shares to relevant DMA
        puma_shares = dma_to_puma[dma_to_puma['dma_code']==dma]

        # Merge shares onto PUMS data
        pums_data_shares = pd.merge(pums_data,puma_shares,on=['STATE','PUMA'],how='inner')

        # Create counts of observations by PUMA
        pums_data_shares['int'] = 1
        pums_data_shares['obs'] = pums_data_shares.groupby(['STATE','PUMA'])['int'].transform('sum')

        # Sampling probability
        pums_data_shares['sprob'] = pums_data_shares['dma_share']/pums_data_shares['obs']
        print(pums_data_shares.loc[pums_data_shares['dma_code']==dma])

        # Draw from empirical distribution
        pums_sample_dma = pums_data_shares.sample(n=ndraw, replace=True, weights='sprob', random_state=1)

        # Append to full dataset
        rel_vars = ['YEAR','dma_code','hhmember'] + hhids + pids
        pums_sample_dma = pums_sample_dma[rel_vars]
        return(pums_sample_dma)

def assemble_nodes_weights(num_rc,level):

        # Set integration objects
        integration = pyblp.Integration('grid', level)
        nodes_weights_in = pyblp.build_integration(integration, num_rc)

        # Create data frame of nodes and weights
        weights = pd.DataFrame.from_records(nodes_weights_in.weights,columns=['weight'])

        cols = ['nodes'+str(ii) for ii in range(num_rc)]
        nodes = pd.DataFrame.from_records(nodes_weights_in.nodes,columns=cols)
        nodes_weights = pd.concat([weights, nodes], axis=1)
        return(nodes_weights)

def assemble_agent_data(year,period,month_or_quarter,dma,hhids,pids,nodes_weights,dma_to_puma,pums_data):

        # Determine number of draws
        ndraw = nodes_weights.shape[0]

        # Draw from empirical distribution for the given year and quarter
        demographics = sample_demographics(year,dma,hhids,pids,ndraw,dma_to_puma,pums_data)

        # Concatenate with nodes and weights
        nodes_weights.reset_index(drop=True, inplace=True)
        demographics.reset_index(drop=True, inplace=True)
        agent_data = pd.concat([nodes_weights, demographics], axis=1)
        agent_data[month_or_quarter] = period
        return(agent_data)

# Log file
log_out = open("assemble_agent_data.log","a")
sys.stdout = log_out

# Set up inputs and run
if len(sys.argv) != 7:
    print('Error: There must be six arguments.')
    sys.exit()

years_str = sys.argv[1].split(',')
years = [int(yy) for yy in years_str]
periods_str = sys.argv[2].split(',')
periods = [int(pp) for pp in periods_str]
hhids = sys.argv[3].split(',')
pids = sys.argv[4].split(',')
level_str = sys.argv[5].split(',')
level = [int(ll) for ll in level_str]
num_rc_str = sys.argv[6].split(',')
num_rc = [int(nn) for nn in num_rc_str]

# Month or quarter
if periods[0]==4:
        month_or_quarter = 'quarter'
elif periods[0]==12:
        month_or_quarter = 'month'
else:
        print('Must specify either 4 or 12 periods.')

if (month_or_quarter == 'quarter') | (month_or_quarter == 'month'):
        # Assemble nodes and weights
        nodes_weights = assemble_nodes_weights(num_rc[0],level[0])

        # Loop over years, quarters, and DMAs
        count = 0
        for yr in years:

                # List of unique DMAs
                dma_to_puma = pull_dma_shares(yr)
                dma_unique = dma_to_puma['dma_code'].drop_duplicates()

                # PUMS data
                pums_data = import_pums(yr,hhids,pids)

                for pp in range(1,periods[0]+1):

                        for dd in dma_unique:

                                # Counter
                                count += 1
                                print(str(yr)+'P'+str(pp)+'DMA'+dd)

                                agents = assemble_agent_data(yr,pp,month_or_quarter,dd,hhids,pids,nodes_weights,dma_to_puma,pums_data)

                                # Append to full dataset
                                if count == 1:
                                        agent_full = agents
                                else:
                                        agent_full = agent_full.append(agents,ignore_index=True)

        # Export to csv
        agent_full = agent_full[['YEAR',month_or_quarter,'dma_code','weight','nodes0','nodes1','hhmember'] + hhids + pids]
        agent_full = agent_full.rename(columns = {'YEAR' : 'year'})
        out_file = 'Clean/agent_data_' + month_or_quarter + '.csv'

        agent_full.to_csv (out_file, index = None, header=True)

log_out.close()
