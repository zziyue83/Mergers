import pandas as pd
import sys

def marketSize(product, quarterOrMonth):
    market_size = pd.DataFrame()
    chunks = pd.read_csv("../../GeneratedData/" + product + "_dma_" + quarterOrMonth + "_upc_top100.tsv", delimiter = "\t", chunksize = 1000000)
    for data_chunk in chunks:
        market_size_chunk = data_chunk.groupby(['dma_code', quarterOrMonth]).agg({'volume': 'sum'})
        if market_size.empty:
            market_size = market_size_chunk
        else:
            market_size = market_size.add(market_size_chunk, fill_value=0)
    market_size.to_csv("../../GeneratedData/" + product + "_market_size_" + quarterOrMonth + ".tsv", sep = '\t', encoding = 'utf-8')

if len(sys.argv) < 2:
    print("Not enough arguments")
    sys.exit()

product = sys.argv[1]
quarterOrMonth = sys.argv[2]
marketSize(product, quarterOrMonth)
