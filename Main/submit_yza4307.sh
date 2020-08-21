#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 100:00:00
#SBATCH --mail-user=yintianzhan2021@u.northwestern.edu
#SBATCH --mem=20G
#SBATCH --nodes=1

module load python/anaconda3.6
python get_corr_matrix.py 1912896020_1 0.96
