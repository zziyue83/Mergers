import pandas as pd
import numpy as np
import sys

def unit_conversion(products, quarterOrMonth):
    for product in products:
        if product == 'CANDY':
            CANDY_df = pd.read_csv("../../GeneratedData/" + product + "_dma_" + quarterOrMonth + "_upc_top100.tsv", delimiter = "\t", index_col = 0)
            CANDY_df['volume_original_unit'] = CANDY_df['volume']
            CANDY_df.to_csv("../../GeneratedData/" + product + "_dma_" + quarterOrMonth + "_upc_top100_unit_converted.tsv", sep = '\t', encoding = 'utf-8')
            package_size_CANDY_median = np.nanmedian(CANDY_df['size1_amount'])
        if product == 'GUM':
            GUM_df = pd.read_csv("../../GeneratedData/" + product + "_dma_" + quarterOrMonth + "_upc_top100.tsv", delimiter = "\t", index_col = 0)
            package_size_GUM_median = np.nanmedian(GUM_df['size1_amount'])
            GUM_df['volume_original_unit'] = GUM_df['volume']
            GUM_df['volume'] = GUM_df['volume']/package_size_GUM_median*package_size_CANDY_median
            GUM_df.to_csv("../../GeneratedData/" + product + "_dma_" + quarterOrMonth + "_upc_top100_unit_converted.tsv", sep = '\t', encoding = 'utf-8')

if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

quarterOrMonth = sys.argv[1]
products = [sys.argv[2],sys.argv[3]]
unit_conversion(products, quarterOrMonth)
