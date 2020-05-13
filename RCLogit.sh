#!/bin/bash
#SBATCH --job-name="demand estimation random coeffcient logit regression"
#SBATCH -A b1048
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 4:00:00
#SBATCH -p buyin
#SBATCH --mail-user=yintianzhan2021@u.northwestern.edu
#SBATCH --mem=40G

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
python RCLogit.py month BEER 2006 2009
