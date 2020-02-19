import pandas as pd

def MarketShare(nupc = 300, year, product):
    path = "../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv"
    area_month_upc = pd.read_csv(path, delimiter = "\t")
    area_month_upc['sale'] = area_month_upc['units']*area_month_upc['prmult']*area_month_upc['price']
    aggregation_function = {'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first','store_code_uc':'first'}
