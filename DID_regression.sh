#!/bin/bash
#SBATCH --job-name="DID regression"
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
python DID_regression.py CANDY month NoMktShare 200805
python DID_regression.py CANDY month MktShare 200805
python DID_regression.py CANDY quarter NoMktShare 2008Q2
python DID_regression.py CANDY quarter MktShare 2008Q2
pdflatex CANDY_GUM_DID_MktShare_month.tex
pdflatex CANDY_GUM_DID_NoMktShare_month.tex
pdflatex CANDY_GUM_DID_MktShare_quarter.tex
pdflatex CANDY_GUM_DID_NoMktShare_quarter.tex
pdflatex CANDY_GUM_DID_MktShare_month_demographics_inflation_adjusted.tex
pdflatex CANDY_GUM_DID_NoMktShare_month_demographics_inflation_adjusted.tex
pdflatex CANDY_GUM_DID_MktShare_quarter_demographics_inflation_adjusted.tex
pdflatex CANDY_GUM_DID_NoMktShare_quarter_demographics_inflation_adjusted.tex
