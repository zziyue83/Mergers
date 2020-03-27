#!/bin/bash
#SBATCH --job-name="aggregate movement files"
#SBATCH -A p30927
#SBATCH -p short
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 4
#SBATCH -t 1:00:00
#SBATCH --mail-user=yintianzhan2021@u.northwestern.edu
#SBATCH --array=1
#SBATCH --mem=0G
#SBATCH --nodes=1

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
python AggregateToQuarter.py 2006 2009 BEER
# python test1.py
