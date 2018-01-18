#!/bin/bash

#SBATCH -A iPlant-Collabs
#SBATCH -N 1
#SBATCH -n 4
#SBATCH -t 00:30:00
#SBATCH -p development
#SBATCH -J mublast
#SBATCH --mail-type BEGIN,END,FAIL
#SBATCH --mail-user jklynch@email.arizona.edu

module load irods
iget -f /iplant/home/jklynch/data/muscope/blast/test.fa $SCRATCH/muscope-blast

ls -l $SCRATCH/muscope-blast

OUT_DIR="$SCRATCH/muscope-blast/test"

if [[ -d $OUT_DIR ]]; then
  rm -rf $OUT_DIR
fi

run.sh -q "$SCRATCH/muscope-blast/test.fa" -o $OUT_DIR
