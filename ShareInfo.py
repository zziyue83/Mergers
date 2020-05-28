import pandas as pd

def ShareInfo(product,frequency):
    data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
    print(data.columns)
    print(data.head())
    data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    share_info = data[['dma_code_'+frequency,'market_share']]
    markets = share_info.groupby('dma_code_'+frequency)

    median = markets.median()
    median = median.rename(columns={'market_share':'median'})
    print(median)
    min = markets.min()
    min = min.rename(columns={'market_share':'min'})
    print(min)
    max = markets.max()
    max = max.rename(columns={'market_share':'max'})
    print(max)
    mean = markets.mean()
    mean = mean.rename(columns={'market_share':'mean'})
    print(mean)
    sum = markets.sum()
    sum = sum.rename(columns={'market_share':'sum'})
    print(sum)

    median['min'] = min['min']
    median['max'] = max['max']
    median['mean'] = mean['mean']
    median['sum'] = sum['sum']
    print(median.head())

    median.to_csv('ShareInfo.csv',sep = ',')

ShareInfo('BEER','month')
