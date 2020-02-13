#!/bin/bash
#SBATCH --job-name="[[job name]]"
#SBATCH -A b1048
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 4:00:00
#SBATCH -p buyin
#SBATCH --mail-user=[[email]]
#SBATCH --mem=4G

module load python
cd [[path to working directory]]
python [[script name]]
