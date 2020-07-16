#!/bin/bash
#SBATCH --job-name="nested with 2 groups"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 4
#SBATCH -t 0
#SBATCH --mail-user=ziyuechen2022@u.northwestern.edu
#SBATCH --array=1
#SBATCH --mem=0
#SBATCH --nodes=1

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
python candy_gum_nested_into_two_groups.py month CANDY GUM sugar cocoa_beans
