#!/usr/bin/python

import sys
import os

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))

module = sys.argv[1]
module = str(module)
print(module)

years = ['2006','2007','2008','2009']

for year in years:
    rootdir = "/projects/b1048/gillanes/Mergers/Data/nielsen_extracts/RMS/"+year+"/Movement_Files/"+module+year
    for file in os.listdir(rootdir):
        print(file)
