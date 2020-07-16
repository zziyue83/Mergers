import pandas as pd
#import numpy as np
# products_path = "../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
df = pd.read_csv("products.tsv", delimiter = "\t", encoding = "cp1252", header = 0)

import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
import re
html = urllib.request.urlopen('https://en.wikipedia.org/wiki/SABMiller_brands').read()
soup = BeautifulSoup(html, 'html.parser')
brandsWiki = re.findall('<li>(.*)<', soup.decode())
b_ = map(lambda x: x.split(' (')[0].replace('</li>',''), brandsWiki)
b_1 = list(b_)
b_1.index('<a class="mw-redirect" href="/wiki/Viva_(beverage)" title="Viva')
b_1 = b_1[:195]
for i in range(len(b_1)):
    if b_1[i][0] == '<':
        #print(b_1[i])
        b_1[i] = 0
        
b_1 = list(map(lambda x: x.split('<')[0], list(filter(lambda a: a != 0, b_1))))
b_1.extend(('Carling Black Label','Castle Lager','Castle Lite','Castle Milk Stout','Castle Free','Miller Genuine Draft','Peroni','Fosters','Chibuku Opaque Beer','Pilsner Urquell','Coca-Cola','Guaraná Backus','Sparletta','Viva','Dreher Sörgyárak','miller'))
b_1 = map(lambda x:x.upper(), b_1)
brands = list(b_1)
df['TargetName'] = df['brand_descr'].apply(lambda x: 'SABMiller PLC' if (x in brands) else 'None')
dfTarget = df[df['TargetName'] == 'SABMiller PLC']
product_groups = list(set(dfTarget['product_group_descr']))
groupfreq = {}
for group in product_groups:
    freq = len(list(set(dfTarget['brand_descr'][dfTarget['product_group_descr'] == group])))
    groupfreq[group] = freq
    
groupfreq_ = {key:val for key, val in groupfreq.items() if val != 0}

df_ = pd.DataFrame([groupfreq_]).T.rename(columns={0: '# of products (Target)'}).rename_axis('product group')
dfSAB = df_.sort_values('# of products (Target)', ascending=False)
dfSAB.to_csv("SAB_draft1.tsv")
