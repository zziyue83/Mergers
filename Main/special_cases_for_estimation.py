import pandas as pd

def special_cases_for_estimation(code, df):
    if code == '1912896020_1':
        df = df[df['alcoholic'] == 1]
    
    return df
