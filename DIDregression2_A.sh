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
<<<<<<< HEAD
<<<<<<< HEAD
python DIDregression2_A.py quarter CANDY GUM
=======
python DIDregression2_A.py quarter BEER
>>>>>>> 60263bd182d4190d5acc2accfbd420a51a7136d3
=======
python DIDregression2_A.py month BEER
>>>>>>> 750777f4f3b39449f848ff024d61e0041a04100a
