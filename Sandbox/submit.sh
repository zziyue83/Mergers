#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 100:00:00
#SBATCH --mail-user=jdsalas@u.northwestern.edu
#SBATCH --mem=45G
#SBATCH --nodes=1

module load python/anaconda3.6
python -m pip install pandas --user
python -m pip install pandasql --user
python -m pip install pyblp --user
python -m pip install linearmodels --user
python -m pip install pyhdfe --user
cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox
python Parties_Count.py
