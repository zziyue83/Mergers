import pandas as pd
years = [2006,2007,2008,2009]
Form_FrequencyTable = pd.DataFrame()
Type_FrequencyTable = pd.DataFrame()
Variety_FrequencyTable = pd.DataFrame()

for year in years:
    year = str(year)
    chunks = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_" + year + "_with_features.tsv", sep = '\t', encoding = 'utf-8', chunksize = 100000)
    for data_chunk in chunks:
        Form_FrequencyTable_per_chunk = data_chunk['form_descr'].value_counts(dropna=False)
        if Form_FrequencyTable.empty:
            Form_FrequencyTable = Form_FrequencyTable_per_chunk
            print(Form_FrequencyTable)
        else:
            Form_FrequencyTable = Form_FrequencyTable.add(Form_FrequencyTable_per_chunk, fill_value=0)

        Type_FrequencyTable_per_chunk = data_chunk['type_descr'].value_counts(dropna=False)
        if Type_FrequencyTable.empty:
            Type_FrequencyTable = Type_FrequencyTable_per_chunk
            print(Type_FrequencyTable)
        else:
            Type_FrequencyTable = Type_FrequencyTable.add(Type_FrequencyTable_per_chunk, fill_value=0)

        Variety_FrequencyTable_per_chunk = data_chunk['variety_descr'].value_counts(dropna=False)
        if Variety_FrequencyTable.empty:
            Variety_FrequencyTable = Variety_FrequencyTable_per_chunk
            print(Variety_FrequencyTable)
        else:
            Variety_FrequencyTable = Variety_FrequencyTable.add(Variety_FrequencyTable_per_chunk, fill_value=0)
    print(Form_FrequencyTable)
    print(Type_FrequencyTable)
    print(Variety_FrequencyTable)

Form_FrequencyTable = Form_FrequencyTable.astype('int32')
Form_FrequencyTable.to_csv("../../GeneratedData/CANDY_dma_month_upc_form_frequency_table.tsv", sep = '\t', encoding = 'utf-8')

    Type_FrequencyTable = Type_FrequencyTable.astype('int32')
    Type_FrequencyTable.to_csv("../../GeneratedData/CANDY_dma_month_upc_type_frequency_table.tsv", sep = '\t', encoding = 'utf-8')

    Variety_FrequencyTable = Variety_FrequencyTable.astype('int32')
    Variety_FrequencyTable.to_csv("../../GeneratedData/CANDY_dma_month_upc_variety_frequency_table.tsv", sep = '\t', encoding = 'utf-8')
