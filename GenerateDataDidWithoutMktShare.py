import pandas as pd
from tqdm import tqdm
import sys

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def MakeOwnerDummy(mergers, controls):
    ownerDummyDf = pd.DataFrame(columns = ['owner', 'merging'])
    for merger in mergers:
        ownerDummyDf = ownerDummyDf.append({'owner': merger, 'merging':1})
    for control in controls:
        ownerDummyDf = ownerDummyDf.append({'owner': control, 'merging':0})
    return ownerDummyDf

def AddOwner(product, years, mergers, controls):
    added_owner_list = []
    ownerDummyDf = MakeOwnerDummy(mergers, controls)
    print(ownerDummyDf)
    years = list(map(str,years))
    brandsCumuYear = []
    owners = pd.read_excel("Top 100 "+product+".xlsx", delimiter = '\t', index_col = 0)
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
AddOwner(product, years, ['Molson Coors', 'SABMiller'], ['Anheuser-Busch', 'InBev'])
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91
