#!/bin/bash

#SBATCH -A iPlant-Collabs
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 00:30:00
#SBATCH -p normal
#SBATCH -J ohana-blast-test
#SBATCH --mail-type BEGIN,END,FAIL
#SBATCH --mail-user jklynch@email.arizona.edu

#module load irods
#iget -f /iplant/home/jklynch/data/muscope/blast/test.fa $SCRATCH/muscope-blast

#ls -l $SCRATCH/muscope-blast

OUT_DIR="$SCRATCH/ohana-blast/test"
if [[ -d $OUT_DIR ]]; then
  rm -rf $OUT_DIR
fi

run.sh -q test.fa -o $OUT_DIR
