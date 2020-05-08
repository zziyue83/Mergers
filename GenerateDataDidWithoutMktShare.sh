#!/bin/bash
#SBATCH --job-name="panel data generation"
#SBATCH -A b1048
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 4:00:00
#SBATCH -p buyin
#SBATCH --mail-user=yintianzhan2021@u.northwestern.edu
#SBATCH --mem=40G

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
# python GenerateDataDidWithoutMktShare.py 2006 2009 BEER month 200807 200601
# python GenerateDataDidWithoutMktShare.py 2006 2009 BEER quarter 2008Q3 200601
python GenerateDataDidWithoutMktShare.py 2006 2009 CANDY month 200805 200601
# python GenerateDataDidWithoutMktShare.py 2006 2009 CANDY quarter 2008Q2 200601
# python GenerateDataDidWithoutMktShare.py 2006 2009 GUM month 200805 200601
# python GenerateDataDidWithoutMktShare.py 2006 2009 GUM quarter 2008Q2 200601
