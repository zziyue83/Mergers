#!/bin/bash
#SBATCH --job-name="millercoors select products"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 1:00:00
#SBATCH --mail-user=yintianzhan2021@u.northwestern.edu
#SBATCH --mem=15G
#SBATCH --nodes=1

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Main
python select_products.py 1912896020_1 
