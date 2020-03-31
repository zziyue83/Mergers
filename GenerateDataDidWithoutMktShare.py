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
    print(ownerDummyDf)
    return ownerDummyDf

def MakeTimeDummy(times, mergingt, startt, frequency):
    timeDummyDf = pd.DataFrame(columns = ['t', 'post_merger','quarters_since_start'])
    if frequency == 'quarter':
        merging_year = int(mergingt[0:4])
        merging_q = int(mergingt[-1])
        start_year = int(startt[0:4])
        start_q = int(startt[-1])
        for quarter in times:
            year = int(quarter[0:4])
            q = int(quarter[-1])
            if (year>= merging_year and q >= merging_q) or (year > merging_year):
                post_merger = 1
            else:
                post_merger = 0
            quarters_since_start = (year - start_year) * 4 + (q - start_q)
            timeDummyDf = timeDummyDf.append({'t': quarter, 'post_merger':post_merger, 'quarters_since_start':quarters_since_start}, ignore_index = True)
    elif frequency == 'month':
        merging_year = int(mergingt[0:4])
        merging_m = int(mergingt[4:])
        start_year = int(startt[0:4])
        start_m = int(startt[4:])
        for month in times:
            year = int(month[0:4])
            m = int(month[4:])
            if (year>= merging_year and m >= merging_m) or (year > merging_year):
                post_merger = 1
            else:
                post_merger = 0
            months_since_start = (year - start_year) * 12 + (m - start_m)
            timeDummyDf = timeDummyDf.append({'t': month, 'post_merger':post_merger, 'months_since_start':months_since_start}, ignore_index = True)
    else:
        return None
    return timeDummyDf

def AddOwnerandTimeVariables(product, years, mergers, mergingt, startt, frequency):
    owners = pd.read_csv("Top 100 "+product+".csv", delimiter = ',')
    print(owners.columns)
    all_owners = owners['owner initial'].unique()
    ownerDummyDf = MakeOwnerDummy(mergers, all_owners)
    years = list(map(str,years))

    DID_list = []
    for year in years:
        movement = pd.read_csv("../../GeneratedData/"+product+"_dma_"+frequency+"_upc_"+year+".tsv", delimiter = '\t', chunksize = 1000000)
        for data_chunk in tqdm(movement):
            print(data_chunk.columns)
            added_owner = data_chunk.merge(owners, how = 'inner', left_on = 'brand_descr', right_on = 'brand_code_descr')
            added_owner = added_owner.merge(ownerDummyDf, how = 'inner', left_on = 'owner initial', right_on = 'owner')
            added_owner[frequency+'_str'] = added_owner[frequency].astype(str)
            times = added_owner[frequency+'_str'].unique()
            timeDummyDf = MakeTimeDummy(times, mergingt, startt, frequency)
            added_time = added_owner.merge(timeDummyDf, how = 'inner', left_on = frequency+'_str', right_on = 't')
            DID_list.append(added_time)

    savePath = "../../GeneratedData/"+product+"_DID_without_share_"+frequency+".tsv"
    DID_agg = pd.concat(DID_list)
    DID_agg = DID_agg[['upc','price','dma_code','brand_code_uc','brand_descr_x','post_merger',frequency+'s_since_start',frequency,'owner','merging']]
    DID_agg = DID_agg.rename(columns = {'brand_descr_x': 'brand_descr'})
    DID_agg.to_csv(savePath, sep = '\t')

if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
frequency = sys.argv[4]
mergingt = sys.argv[5]
startt = sys.argv[6]
years = GenerateYearList(start, end)
print(product)
print(years)
print(frequency)
AddOwnerandTimeVariables(product, years, ['Mars', 'Wrigley'],mergingt,startt, frequency)
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91
