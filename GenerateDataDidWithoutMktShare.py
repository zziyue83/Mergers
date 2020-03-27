import pandas as pd
from tqdm import tqdm
import sys
import datetime

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def MakeOwnerDummy(mergers, controls):
    ownerDummyDf = pd.DataFrame(columns = ['owner', 'merging'])
    for merger in mergers:
        ownerDummyDf = ownerDummyDf.append({'owner': merger, 'merging':1}, ignore_index = True)
    for control in controls:
        ownerDummyDf = ownerDummyDf.append({'owner': control, 'merging':0}, ignore_index = True)
    return ownerDummyDf

def MakeTimeDummy(quarters, mergingq, startq):
    timeDummyDf = pd.DataFrame(columns = ['quarter', 'post_merger','quarters_since_start'])
    merging_year = int(mergingq[0:4])
    merging_q = int(mergingq[-1])
    start_year = int(startq[0:4])
    start_q = int(startq[-1])
    for quarter in quarters:
        year = int(quarter[0:4])
        q = int(quarter[-1])
        if year>= merging_year and q >= merging_q:
            post_merger = 1
        else:
            post_merger = 0
        quarters_since_start = (year - start_year) * 4 + (q - start_q)
        timeDummyDf = timeDummyDf.append({'quarter': quarter, 'post_merger':post_merger, 'quarters_since_start':quarters_since_start}, ignore_index = True)
    return timeDummyDf

def AddOwnerandTimeVariables(product, years, mergers, controls, mergingq, startq):
    added_owner_list = []
    ownerDummyDf = MakeOwnerDummy(mergers, controls)
    print(ownerDummyDf)
    years = list(map(str,years))
    brandsCumuYear = []
    owners = pd.read_csv("Top 100 "+product+".csv", delimiter = ',')
    print(owners)
    for year in years:
        # firstFile = True
        movement = pd.read_csv("../../GeneratedData/"+product+"_dma_quarter_upc_"+year+".tsv", delimiter = '\t', index_col = "upc", chunksize = 1000000)
        for data_chunk in tqdm(movement):
            addedOwner = data_chunk.merge(owners, how = 'inner', left_on = 'brand_code_uc', right_on = 'brand_code_uc')
            added_owner_list.append(addedOwner)
            # if firstFile:
            #     merged.to_csv(savePath, sep = '\t')
            #     firstFile = False
            # else:
            #     merged.to_csv(savePath, sep = '\t', header = False, mode = 'a')
    savePath = "../../GeneratedData/"+product+"_DID_without_Share.tsv"
    added_owner_agg = pd.concat(added_owner_list)
    DID_data = added_owner_agg.merge(ownerDummyDf, how = 'inner', left_on = 'owner initial', right_on = 'owner')
    DID_data['quarter_str'] = DID_data['quarter'].to_string()
    quarters = DIA_data['quarter_datatime'].unique()
    timeDummyDf = MakeTimeDummy(quarters, mergingq, startq)
    DID_data = DID_data.merge(timeDummyDf, how = 'inner', left_on = 'quarter_str', right_on = 'quarter')
    DID_data.to_csv(savePath, sep = '\t')




if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
years = GenerateYearList(start, end)
print(product)
print(years)
AddOwnerandTimeVariables(product, years, ['Molson Coors', 'SABMiller'], ['Anheuser-Busch', 'InBev'],'2008Q3','2006Q1')
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91
