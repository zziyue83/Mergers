import pandas as pd
from tqdm import tqdm
import sys

def CreateFrequencyTable(product, years):
    freqTables = {}
    # Form_FrequencyTable = pd.DataFrame()
    # Type_FrequencyTable = pd.DataFrame()
    # Variety_FrequencyTable = pd.DataFrame()
    for year in years:
        year = str(year)
        chunks = pd.read_csv("../../GeneratedData/"+product+"_dma_month_upc_" + year + "_with_features.tsv", sep = '\t', encoding = 'utf-8', chunksize = 100000)
        for data_chunk in tqdm(chunks):
            columns = data_chunk.columns
            for column in columns:
                if column not in freqTables:
                    freqTables[column] = pd.DataFrame()
                frequencyTable_per_chunk = data_chunk[column].value_counts(dropna=False)
                if freqTables[column].empty:
                    freqTables[column] = frequencyTable_per_chunk
                    print(Form_FrequencyTable)
                else:
                    freqTables[column] = freqTables[column].add(frequencyTable_per_chunk, fill_value=0)
    output = product + "_Frequency_Table.xlsx"
    with pd.ExcelWriter(output) as writer:
        for column in freqTables:
            freqTables[column].to_excel(writer,sheet_name = column)
            # Type_FrequencyTable_per_chunk = data_chunk['type_descr'].value_counts(dropna=False)
            # if Type_FrequencyTable.empty:
            #     Type_FrequencyTable = Type_FrequencyTable_per_chunk
            #     print(Type_FrequencyTable)
            # else:
            #     Type_FrequencyTable = Type_FrequencyTable.add(Type_FrequencyTable_per_chunk, fill_value=0)
            #
            # Variety_FrequencyTable_per_chunk = data_chunk['variety_descr'].value_counts(dropna=False)
            # if Variety_FrequencyTable.empty:
            #     Variety_FrequencyTable = Variety_FrequencyTable_per_chunk
            #     print(Variety_FrequencyTable)
            # else:
            #     Variety_FrequencyTable = Variety_FrequencyTable.add(Variety_FrequencyTable_per_chunk, fill_value=0)
        # print(Form_FrequencyTable)
        # print(Type_FrequencyTable)
        # print(Variety_FrequencyTable)

    # Form_FrequencyTable = Form_FrequencyTable.astype('int32')
    # Form_FrequencyTable.to_csv("../../GeneratedData/CANDY_dma_month_upc_form_frequency_table.tsv", sep = '\t', encoding = 'utf-8')
    #
    # Type_FrequencyTable = Type_FrequencyTable.astype('int32')
    # Type_FrequencyTable.to_csv("../../GeneratedData/CANDY_dma_month_upc_type_frequency_table.tsv", sep = '\t', encoding = 'utf-8')
    #
    # Variety_FrequencyTable = Variety_FrequencyTable.astype('int32')
    # Variety_FrequencyTable.to_csv("../../GeneratedData/CANDY_dma_month_upc_variety_frequency_table.tsv", sep = '\t', encoding = 'utf-8')

start = sys.argv[1]
end = sys.argv[2]
product = sys.argv[3]
years = GenerateYearList(start, end)
print(product)
print(years)
AddExtraFeatures(product, years)
