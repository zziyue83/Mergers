#!/bin/bash
#SBATCH --job-name="DID regression in one file"
#SBATCH -A b1048
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 4:00:00
#SBATCH -p buyin
#SBATCH --mail-user=yintianzhan2021@u.northwestern.edu
#SBATCH --mem=20G

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
python GenerateDataDidWithoutMktShare.py 2006 2009 BEER quarter 2008Q3 200601
python DID_regression.py BEER quarter NoMktShare 2008Q3
python DID_regression.py BEER quarter MktShare 2008Q3
python GenerateDataDidWithoutMktShare.py 2006 2009 BEER month 200807 200601
python DID_regression.py BEER month NoMktShare 200807
python DID_regression.py BEER month MktShare 200807
pdflatex BEER_DID_MktShare_month.tex
pdflatex BEER_DID_NoMktShare_month.tex
pdflatex BEER_DID_MktShare_quarter.tex
pdflatex BEER_DID_NoMktShare_quarter.tex
