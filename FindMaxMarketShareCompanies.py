import pandas as pd
# <<<<<<< HEAD

# def MarketShare(nupc = 300, year, product):
#     path = "../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv"
#     area_month_upc = pd.read_csv(path, delimiter = "\t")
#     area_month_upc['sale'] = area_month_upc['units']*area_month_upc['prmult']*area_month_upc['price']
#     aggregation_function = {'units': 'sum', 'prmult':'mean', 'price':'mean', 'feature': 'first','display':'first','store_code_uc':'first'}
# =======
import sys

def GenerateYearList(start, end):
    s = int(start)
    e = int(end)
    return list(range(s, e+1))

def MarketShare(product, years):
    years = list(map(str,years))
    brandsCumuYear = []
    for year in years:
        products = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_"+year+".tsv", sep = '\t', encoding = 'utf-8', header = 0, index_col = "upc")
        productMap = products.to_dict()
        brandsVolume = products.groupby(['month','brand_code_uc']).agg({'volume': 'sum', 'brand_code_descr': 'first'}).set_index('brand_code_uc')
        brandsMap = brandsVolume.to_dict()
        print(brandsVolume.iloc[0])
        top100forEachMonth = brandsVolume.groupby(level=0)['volume'].nlargest(100)
        brandsCumuYear.extend(list(set(top100forEachMonth.index.get_level_values(2))))
        print(len(brandsCumuYear))

    brands = list(set(brandsCumuYear))
    print(brands)
    return brands

if len(sys.argv) < 4:
    print("Not enough arguments")
    sys.exit()

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
years = GenerateYearList(start, end)
print(years)
MarketShare(product, years)
# >>>>>>> fc0f14f7f4cc63df8fc9b9cfc1a730ed3a969f91
