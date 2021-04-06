#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 600:00:00
#SBATCH --mail-user=jdsalas@u.northwestern.edu
#SBATCH --mem=100G
#SBATCH -n 12
cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Sandbox
module load python/anaconda3.6
module load parallel

parallel -j12 "python Did_interact_parallel.py {}" ::: ../../../All/*
