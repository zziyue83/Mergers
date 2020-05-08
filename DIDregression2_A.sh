#!/bin/bash
#SBATCH --job-name="DID2"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 4
#SBATCH -t 1:00:00
#SBATCH --mail-user=ziyuechen2022@u.northwestern.edu
#SBATCH --array=1
#SBATCH --mem=40G
#SBATCH --nodes=1

module load python/anaconda3.6
cd /projects/b1048/gillanes/Mergers/Codes/Mergers
python DIDregression2_A.py quarter BEER
=======
python DIDregression2_A.py month BEER
>>>>>>> 750777f4f3b39449f848ff024d61e0041a04100a
