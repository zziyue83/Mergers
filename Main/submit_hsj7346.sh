#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 12:00:00
#SBATCH --mail-user=heejung2020@u.northwestern.edu
#SBATCH --mem=15G
#SBATCH --nodes=1

module load python/anaconda3.6

python -m pip install --upgrade linearmodels --user

cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Main
python select_products.py 1920449020_1
