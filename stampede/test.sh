#!/bin/bash

#SBATCH -A iPlant-Collabs
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 02:00:00
#SBATCH -p normal
#SBATCH -J mublast
#SBATCH --mail-type BEGIN,END,FAIL
#SBATCH --mail-user kyclark@email.arizona.edu

run.sh -q "$SCRATCH/muscope-blast/test.fa" -o "$SCRATCH/muscope-blast/test"
