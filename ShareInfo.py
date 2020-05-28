import pandas as pd

def ShareInfo(product,frequency):
    data = pd.read_csv("../../GeneratedData/" + product + '_'+ frequency + "_pre_model_with_distance.tsv", delimiter = '\t')
    print(data.columns)
    print(data.head())
    data['dma_code_'+frequency] = data['dma_code'].astype(str)+data[frequency].astype(str)
    share_info = data[['dma_code_'+frequency,'market_share']]
    mean = share_info.groupby('dma_code_'+frequency).mean()
    print(mean)

ShareInfo('BEER','month')
