#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 100:00:00
#SBATCH --mail-user=ziyuechen2022@u.northwestern.edu
#SBATCH --mem=0
#SBATCH --nodes=1

module load python/anaconda3.6
python identify_store_brands.py 2033113020_1
