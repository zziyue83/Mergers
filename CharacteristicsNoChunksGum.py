import pandas as pd
import sys

years = [2006,2007,2008,2009]
Form_FrequencyTable = pd.DataFrame()
Flavor_FrequencyTable = pd.DataFrame()
Variety_FrequencyTable = pd.DataFrame()
def GenerateFrequency(product):
    for year in years:
        year = str(year)
        df = pd.read_csv("../../GeneratedData/" + product + "_dma_month_upc_" + year + "_with_features.tsv", sep = '\t', encoding = 'utf-8')
        Form_FrequencyTable_per_year = df['form_descr'].value_counts(dropna=False)
        Flavor_FrequencyTable_per_year = df['flavor_descr'].value_counts(dropna=False)
        Variety_FrequencyTable_per_year = df['variety_descr'].value_counts(dropna=False)
        if year == '2006':
            Form_FrequencyTable = Form_FrequencyTable_per_year
            Flavor_FrequencyTable = Flavor_FrequencyTable_per_year
            Variety_FrequencyTable = Variety_FrequencyTable_per_year
        else:
            Form_FrequencyTable = Form_FrequencyTable.add(Form_FrequencyTable_per_year, fill_value=0)
            Flavor_FrequencyTable = Flavor_FrequencyTable.add(Flavor_FrequencyTable_per_year, fill_value=0)
            Variety_FrequencyTable = Variety_FrequencyTable.add(Variety_FrequencyTable_per_year, fill_value=0)
        print(Form_FrequencyTable)
        print(Flavor_FrequencyTable)
        print(Variety_FrequencyTable)

    Form_FrequencyTable = Form_FrequencyTable.astype('int32')
    Form_FrequencyTable.to_csv("../../GeneratedData/" + product + "_dma_month_upc_form_frequency_table.tsv", sep = '\t', encoding = 'utf-8')

    Flavor_FrequencyTable = Flavor_FrequencyTable.astype('int32')
    Flavor_FrequencyTable.to_csv("../../GeneratedData/" + product + "_dma_month_upc_type_frequency_table.tsv", sep = '\t', encoding = 'utf-8')

    Variety_FrequencyTable = Variety_FrequencyTable.astype('int32')
    Variety_FrequencyTable.to_csv("../../GeneratedData/" + product + "_dma_month_upc_variety_frequency_table.tsv", sep = '\t', encoding = 'utf-8')

product = sys.argv[1]
GenerateFrequency(product)
