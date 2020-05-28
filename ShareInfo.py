import pandas as pd

def ShareInfo(product,frequency):
    data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
    print(data.columns)
    print(data.head())
    data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    share_info = data[['dma_code_'+frequency,'market_share']]
    markets = share_info.groupby('dma_code_'+frequency)
    median = markets.median()
    print(median)
    min = markets.min()
    print(min)
    max = markets.max()
    print(max)
    mean = markets.mean()
    print(mean)
    sum = markets.sum()
    print(sum)

ShareInfo('BEER','month')
