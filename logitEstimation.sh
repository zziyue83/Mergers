#!/bin/bash
#SBATCH --job-name="logit"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 4
#SBATCH -t 100:00:00
#SBATCH --mail-user=ziyuechen2022@u.northwestern.edu
#SBATCH --array=1
#SBATCH --mem=0
#SBATCH --nodes=1

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
python logitEstimation.py quarter CANDY GUM sugar cocoa_beans mint chocolate
