#!/bin/bash

set -u

BIN=$( cd "$( dirname "$0" )" && pwd )
QUERY=""
PCT_ID=".98"
OUT_DIR="$BIN"
NUM_THREADS=12

module load blast

function lc() {
  wc -l "$1" | cut -d ' ' -f 1
}

function HELP() {
  printf "Usage:\n  %s -q QUERY -o OUT_DIR\n\n" $(basename $0)

  echo "Required arguments:"
  echo " -q QUERY"
  echo
  echo "Options:"
  echo
  echo " -p PCT_ID ($PCT_ID)"
  echo " -o OUT_DIR ($OUT_DIR)"
  echo 
  exit 0
}

if [[ $# -eq 0 ]]; then
  HELP
fi

while getopts :o:p:q:h OPT; do
  case $OPT in
    h)
      HELP
      ;;
    o)
      OUT_DIR="$OPTARG"
      ;;
    p)
      PCT_ID="$OPTARG"
      ;;
    q)
      QUERY="$OPTARG"
      ;;
    :)
      echo "Error: Option -$OPTARG requires an argument."
      exit 1
      ;;
    \?)
      echo "Error: Invalid option: -${OPTARG:-""}"
      exit 1
  esac
done

if [[ -d "$OUT_DIR" ]]; then
  mkdir -p "$OUT_DIR"
fi

BLAST_OUT_DIR="$OUT_DIR/blast-out"
if [[ ! -d "$BLAST_OUT_DIR" ]]; then
  mkdir -p "$BLAST_OUT_DIR"
fi

INPUT_FILES=$(mktemp)
if [[ -d $QUERY ]]; then
  find "$QUERY" -type f > "$INPUT_FILES"
else
  echo "$QUERY" > $INPUT_FILES
fi
NUM_INPUT=$(lc "$INPUT_FILES")

if [[ $NUM_INPUT -lt 1 ]]; then
  echo "No input files found"
  exit 1
fi

BLAST_DIR="$WORK/ohana/blast"

if [[ ! -d "$BLAST_DIR" ]]; then
  echo BLAST_DIR \"$BLAST_DIR\" does not exist.
  exit 1
fi

BLAST_DIR=$WORK/ohana/blast
BLAST_ARGS="-perc_identity $PCT_ID -outfmt 6"
PARAM="$$.param"

cat /dev/null > $PARAM # make sure it's empty

i=0
while read INPUT_FILE; do
  BASENAME=$(basename "$INPUT_FILE")

  let i++
  printf "%3d: %s\n" "$i" "$BASENAME"
  EXT="${BASENAME##*.}"
  TYPE="unknown"
  if [[ $EXT == 'fa'    ]] || \
     [[ $EXT == 'fna'   ]] || \
     [[ $EXT == 'fas'   ]] || \
     [[ $EXT == 'fasta' ]] || \
     [[ $EXT == 'ffn'   ]];
  then
    TYPE="dna"
  elif [[ $EXT == 'faa' ]]; then
    TYPE="prot"
  elif [[ $EXT == 'fra' ]]; then
    TYPE="rna"
  fi

  BLAST_TO_DNA=""
  if [[ $TYPE == 'dna' ]]; then 
    BLAST_TO_DNA='blastn'
  elif [[ $TYPE == 'prot' ]]; then
    BLAST_TO_DNA='tblastn'
  else
    echo "Cannot BLAST $BASENAME to DNA (not DNA or prot)"
  fi

  if [[ ${#BLAST_TO_DNA} -gt 0 ]]; then
    echo "$BLAST_TO_DNA -num_threads $NUM_THREADS -perc_identity $PCT_ID -outfmt 6 -db $BLAST_DIR/contigs -query $INPUT_FILE -out $BLAST_OUT_DIR/$BASENAME-contigs" >> $PARAM
    echo "$BLAST_TO_DNA -num_threads $NUM_THREADS -perc_identity $PCT_ID -outfmt 6 -db $BLAST_DIR/genes -query $INPUT_FILE -out $BLAST_OUT_DIR/$BASENAME-genes" >> $PARAM
  fi

  BLAST_TO_PROT=""
  if [[ $TYPE == 'dna' ]]; then 
    BLAST_TO_PROT='blastx'
  elif [[ $TYPE == 'prot' ]]; then
    BLAST_TO_PROT='blastp'
  else
    echo "Cannot BLAST $BASENAME to PROT (not DNA or prot)"
  fi

  if [[ ${#BLAST_TO_PROT} -gt 0 ]]; then
    echo "$BLAST_TO_PROT -num_threads $NUM_THREADS -outfmt 6 -db $BLAST_DIR/proteins -query $INPUT_FILE -out $BLAST_OUT_DIR/$BASENAME-proteins" >> $PARAM
  fi
done < "$INPUT_FILES"

echo "Starting launcher $(date)"
export LAUNCHER_NJOBS=$(lc $PARAM)
export LAUNCHER_NHOSTS=4
export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR=$LAUNCHER_DIR/plugins
export LAUNCHER_RMI=SLURM
export LAUNCHER_JOB_FILE=$PARAM
export LAUNCHER_PPN=4
$LAUNCHER_DIR/paramrun
echo "Ended launcher $(date)"

cat /dev/null > $PARAM

ANNOT_DIR=$OUT_DIR/annots
if [[ ! -d $ANNOT_DIR ]]; then
  mkdir -p $ANNOT_DIR
fi

GENE_HITS=$(mktemp)
find $BLAST_OUT_DIR -size +0c -name \*-genes > $GENE_HITS
while read FILE; do
  BASENAME=$(basename $FILE)
  echo "Annotating $BASENAME"
  python ./annotate.py -b $FILE -a ${WORK}/ohana/sqlite -o $ANNOT_DIR > $ANNOT_DIR/$BASENAME
done < $GENE_HITS

echo "Starting launcher $(date)"
export LAUNCHER_NJOBS=$(lc $PARAM)
$LAUNCHER_DIR/paramrun
echo "Ended launcher $(date)"

rm "$INPUT_FILES"
rm "$PARAM"
