import pandas as pd
import os

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
print(str(script_dir))
# rel_path = "/../../Data/nielsen_extracts/RMS/Master_Files/Latest/products.tsv"
# products_path = os.path.join(script_dir, rel_path)
# products = pd.read_csv(products_path, delimiter = "\t", encoding = "cp1252", header = 0)
# products.iloc[0]
# products.columns
