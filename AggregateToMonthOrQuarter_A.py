import pandas as pd
import sys

def BrandOwner(product):
    brand_owner = pd.read_csv("Top 100 " + product + ".csv", index_col='brand_descr')
    #brand_owner = pd.read_excel("Top 100 " + product + " with owner.xlsx",header = 0,index_col='brand_descr')
    #brand_owner.rename(columns={2006:'owner initial', 2009:'owner last'}, inplace=True)
    #brand_owner = brand_owner.drop([2007,2008], axis = 1)
    return brand_owner

def Aggregate_to_Month(top100brand_data):
    panel_data = top100brand_data.groupby(['upc','dma_code','month']).agg({'volume': 'sum', 'price': 'mean', 'size1_amount': 'first', 'size1_units': 'first', 'brand_descr': 'first', 'owner initial': 'first', 'owner last': 'first'})
    panel_data = panel_data.reset_index()
    panel_data['y-m-d'] = pd.to_datetime(panel_data['month'].values, format='%Y%m')
    panel_data['year'] = panel_data['y-m-d'].dt.year
    panel_data['# month'] = panel_data['y-m-d'].dt.month
    panel_data.to_csv("../../GeneratedData/" + product + "_dma_month_upc_top100.tsv", sep = '\t', encoding = 'utf-8')
    return None
  
def Aggregate_to_Quarter(top100brand_data):
    top100brand_data['y-q'] = pd.to_datetime(top100brand_data['month'].values, format='%Y%m').astype('period[Q]')
    panel_data = top100brand_data.groupby(['upc','dma_code','y-q']).agg({'volume': 'sum', 'price': 'mean', 'size1_amount': 'first', 'size1_units': 'first', 'brand_descr': 'first', 'owner initial': 'first', 'owner last': 'first'})
    panel_data = panel_data.reset_index()
    panel_data['quarter'] = panel_data['y-q'].astype(str)
    panel_data['year'] = panel_data['y-q'].dt.year
    panel_data['# quarter'] = panel_data['y-q'].dt.quarter
    panel_data.to_csv("../../GeneratedData/" + product + "_dma_quarter_upc_top100.tsv", sep = '\t', encoding = 'utf-8')
    return None

def Limit_to_Top100_and_Aggregate_to_quarter_or_month(product, quarterOrmonth):
    years = [2006, 2007, 2008, 2009]
    brand_owner = BrandOwner(product)
    top100brand_data = pd.DataFrame()
    for year in years:
        year = str(year)
        chunks = pd.read_csv("../../GeneratedData/" + product + "_dma_month_upc_" + year + ".tsv", delimiter = "\t", chunksize = 1000000)
        for data_chunk in chunks:
            data_chunk['owner initial'] = data_chunk['brand_descr'].map(brand_owner['owner initial'])
            data_chunk['owner last'] = data_chunk['brand_descr'].map(brand_owner['owner last'])
            if top100brand_data.empty:
                top100brand_data = data_chunk
            else:
                top100brand_data = pd.concat([top100brand_data, data_chunk])
        top100brand_data = top100brand_data.dropna(subset=['owner initial'])
        
    if quarterOrmonth == 'month':
        Aggregate_to_Month(top100brand_data)
    if quarterOrmonth == 'quarter':
        Aggregate_to_Quarter(top100brand_data)
    else:
        print('error')
    
if len(sys.argv) < 3:
    print("Not enough arguments")
    sys.exit()
    
product = sys.argv[1]
quarterOrmonth = sys.argv[2]

Limit_to_Top100_and_Aggregate_to_quarter_or_month(product, quarterOrmonth)
