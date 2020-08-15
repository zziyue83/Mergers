#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 12:00:00
#SBATCH --mail-user=aaronbanks@u.northwestern.edu
#SBATCH --mem=15G
#SBATCH --nodes=1

module load python/anaconda3.6
python -m pip install --upgrade pip --user
python -m pip install --upgrade pyblp --user
python -m pip install --numpy --user
python -m pip install --pandas --user
python -m pip install --pandasql --user
python -m pip install --datetime --user
python -m pip install --tqdm --user
python -m pip install --pickle --user
python -m pip install --upgrade xlrd --user
python -m pip install --upgrade linearmodels --user

cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Main
python select_products.py 1785984020_11



