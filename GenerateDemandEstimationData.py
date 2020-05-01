import pandas as pd
import sys

def GenerateDEData(product, frequency):
    data = pd.read_csv("../../GeneratedData/" + product + "_pre_model_" + frequency + "_with_distance.tsv", delimiter = 't')

    print(data)

frequency = sys.argv[1]
product = sys.argv[2]
GenerateDEData(product, frequency)
