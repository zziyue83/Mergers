#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 4:00:00
#SBATCH --mail-user=jdsalas@u.northwestern.edu
#SBATCH --mem=20G
#SBATCH --nodes=1

module load python/anaconda3.6

cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox
python NL_All_agg.py
