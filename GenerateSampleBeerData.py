import pandas as pd
import os

# script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
# print(str(script_dir))
# print(os.getcwd() + "\n")
# rel_path = "/../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
# products_path = os.path.join(script_dir, rel_path)
products_path = "../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0)
print(products.iloc[0])
print(products.columns)
print("hello")
