#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 10:00:00
#SBATCH --mail-user=yintianzhan2021@u.northwestern.edu
#SBATCH --mem=50G
#SBATCH --nodes=1

cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Main
module load python/anaconda3.6
python all_did_brandlevel.py
