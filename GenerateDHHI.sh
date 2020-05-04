#!/bin/bash
#SBATCH --job-name="DID2"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 4
#SBATCH -t 1:00:00
#SBATCH --mail-user=ziyuechen2022@u.northwestern.edu
#SBATCH --array=1
#SBATCH --mem=20G
#SBATCH --nodes=1

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
python GenerateDHHI.py month 2008 5 CANDY GUM
