import pandas as pd
import sys

def Share(product):
    quantity = pd.DataFrame()
    years = [2006, 2007, 2008, 2009]
    for year in years:
        year = str(year)
        chunks = pd.read_csv("../../GeneratedData/" + product + "_dma_month_upc_" + year + ".tsv", delimiter = "\t", chunksize = 1000000)
        for data_chunk in chunks:
            data_chunk['Qtr'] = pd.to_datetime(data_chunk['month'].values, format='%Y%m').astype('period[Q]')
            quantity_chunk = data_chunk.groupby(['upc','dma_code','Qtr']).agg({'units': 'sum'})
            if quantity.empty:
                quantity = quantity_chunk
            else:
                quantity = quantity.add(quantity_chunk, fill_value=0)
            print(quantity)

    market_size = quantity.reset_index('upc')
    market_size = market_size.groupby(level=[0,1]).agg({'units': 'sum'})
    market_size_dma = market_size.groupby(level=0).agg({'units': 'max'})*1.5
    quantity['market share'] = market_size_dma.div(quantity, level=1, fill_value=0)
    quantity = quantity.reset_index('Qtr')
    quantity['year'] = quantity['Qtr'].dt.year
    quantity['postmerger'] = [0 if x == 2006 or x == 2007 else 1 for x in quantity['year']]
    print(quantity)

product = sys.argv[1]
Share(product)
