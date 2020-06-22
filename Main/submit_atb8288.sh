#!/bin/bash
#SBATCH --job-name="mergers"
#SBATCH -A b1048
#SBATCH -p buyin
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH -c 1
#SBATCH -t 1:00:00
#SBATCH --mail-user=aaronbanks@u.northwestern.edu
#SBATCH --mem=15G
#SBATCH --nodes=1


module load python/anaconda3.6
python -m pip install pandas --user
python -m pip install --upgrade pandas --user
python -m pip install pandasql --user
python -m pip install numpy --user
python -m pip install pyblp --user
python -m pip install tqdm --user
python -m pip install datetime --user

cd /projects/b1048/gillanes/Mergers/Codes/Mergers/Main
python get_units.py 2655951020_4
