import pandas as pd
import os

products_path = "../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0)
beerProducts = products[(products['product_group_descr'].isnotnull()) & (products['product_group_descr'].str.contains("BEER"))]
print(products.iloc[0])
print(beerProducts.iloc[0])
print(beerProducts.shape)
