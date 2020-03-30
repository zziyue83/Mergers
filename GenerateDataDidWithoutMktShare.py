import pandas as pd
from tqdm import tqdm
import sys
import datetime

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def MakeOwnerDummy(mergers, all_owners):
    ownerDummyDf = pd.DataFrame(columns = ['owner', 'merging'])
    for merger in mergers:
        ownerDummyDf = ownerDummyDf.append({'owner': merger, 'merging':1}, ignore_index = True)
    for owner in all_owners:
        if owner not in mergers:
            ownerDummyDf = ownerDummyDf.append({'owner': owner, 'merging':0}, ignore_index = True)
    return ownerDummyDf

def MakeTimeDummy(times, mergingq, startq, frequency):
    timeDummyDf = pd.DataFrame(columns = ['q', 'post_merger','quarters_since_start'])
    if frequency == 'quarter':
        merging_year = int(mergingq[0:4])
        merging_q = int(mergingq[-1])
        start_year = int(startq[0:4])
        start_q = int(startq[-1])
        for quarter in quarters:
            year = int(quarter[0:4])
            q = int(quarter[-1])
            if (year>= merging_year and q >= merging_q) or (year > merging_year):
                post_merger = 1
            else:
                post_merger = 0
            quarters_since_start = (year - start_year) * 4 + (q - start_q)
            timeDummyDf = timeDummyDf.append({'q': quarter, 'post_merger':post_merger, 'quarters_since_start':quarters_since_start}, ignore_index = True)
    return timeDummyDf

def AddOwnerandTimeVariables(product, years, mergers, mergingq, startq, frequency):
    owners = pd.read_csv("Top 100 "+product+".csv", delimiter = ',')
    all_owners = owners['owner initial'].unique()
    ownerDummyDf = MakeOwnerDummy(mergers, all_owners)
    years = list(map(str,years))

    DID_list = []
    for year in years:
        movement = pd.read_csv("../../GeneratedData/"+product+"_dma_"+frequency+"_upc_"+year+".tsv", delimiter = '\t', chunksize = 1000000)
        for data_chunk in tqdm(movement):
            added_owner = data_chunk.merge(owners, how = 'inner', left_on = 'brand_code_uc', right_on = 'brand_code_uc')
            added_owner = added_owner.merge(ownerDummyDf, how = 'inner', left_on = 'owner initial', right_on = 'owner')
            added_owner[frequency+'_str'] = added_owner['quarter'].astype(str)
            times = added_owner[frequency+'_str'].unique()
            timeDummyDf = MakeTimeDummy(times, mergingq, startq, frequency)
            added_time = added_owner.merge(timeDummyDf, how = 'inner', left_on = 'quarter_str', right_on = 'q')
            DID_list.append(added_time)

    savePath = "../../GeneratedData/"+product+"_DID_without_Share.tsv"
    DID_agg = pd.concat(DID_list)
    DID_agg = DID_agg[['upc','price','dma_code','brand_code_uc','brand_descr_x','post_merger','quarters_since_start','quarter','owner','merging']]
    DID_agg = DID_agg.rename(columns = {'brand_descr_x': 'brand_descr'})
    DID_agg.to_csv(savePath, sep = '\t')

if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
frequency = sys.argv[4]
years = GenerateYearList(start, end)
print(product)
print(years)
AddOwnerandTimeVariables(product, years, ['Molson Coors', 'SABMiller'],'2008Q3','2006Q1', frequency)
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91
