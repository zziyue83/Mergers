import json
from urllib.request import urlopen
import pandas as pd

data = pd.read_csv("../../GeneratedData/"+'BEER'+"_DID_without_share_"+'month'+".tsv", delimiter = '\t')
data['upc_str'] = data['upc'].astype(str)
for index, row in data.iterrows():
    upc = row['upc_str']
    url = "https://api.edamam.com/api/food-database/parser?upc="+upc+"&app_id=4237ba9d&app_key=56559448d34967c26665a71a519650e6"
    response = urlopen(url)
    data = json.loads(response.read())
    print(data)


# import json
#
# json_url = urlopen(url)
#
# data = json.loads(json_url.read())
#
# print(data)
# with open('https://api.edamam.com/api/food-database/parser?upc=034100575052&app_id=4237ba9d&app_key=56559448d34967c26665a71a519650e6') as f:
#   data = json.load(f)
#
# # Output: {'name': 'Bob', 'languages': ['English', 'Fench']}
# print(data)
