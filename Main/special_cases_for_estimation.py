import pandas as pd

def special_cases_for_estimation(code, df):
    if code == '1912896020_1':
        df = df[df['alcoholic'] == 1]
        df = df[(df['dma_code'] == 500) | (df['dma_code'] == 501) | (df['dma_code'] == 503) | (df['dma_code'] == 505)]

    return df
