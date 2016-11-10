#!/bin/bash

set -u

module load blast

function lc() {
  wc -l "$1" | cut -d ' ' -f 1
}

function HELP() {
  printf "Usage:\n  %s -q QUERY -o OUT_DIR\n\n" $(basename $0)

  echo "Required arguments:"
  echo " -p PCT_ID"
  echo " -q QUERY"
  echo " -t INPUT_TYPE"
  echo " -o OUT_DIR"
  echo ""
  exit 0
}

if [[ $# -eq 0 ]]; then
  HELP
fi

BIN=$( cd "$( dirname "$0" )" && pwd )
QUERY=""
INPUT_TYPE="dna"
PCT_ID=".98"
OUT_DIR="$BIN"

while getopts :o:p:q:t:h OPT; do
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
    t)
      INPUT_TYPE="$OPTARG"
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
  rm -rf $OUT_DIR/*
else
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

BLAST_DIR="$SCRATCH/ohana/blast"

if [[ ! -d "$BLAST_DIR" ]]; then
  echo BLAST_DIR \"$BLAST_DIR\" does not exist.
  exit 1
fi

BLAST_DIR=$SCRATCH/ohana/blast
BLAST_ARGS="-perc_identity $PCT_ID -outfmt 6"

i=0
while read INPUT_FILE; do
  BASENAME=$(basename "$INPUT_FILE")

  let i++
  printf "%3d: %s\n" "$i" "$BASENAME"

  blastn $BLAST_ARGS -db $BLAST_DIR/contigs -query "$INPUT_FILE" -out "$BLAST_OUT_DIR/$BASENAME-contigs"
  blastn $BLAST_ARGS -db $BLAST_DIR/genes -query "$INPUT_FILE" -out "$BLAST_OUT_DIR/$BASENAME-genes"
  blastx $BLAST_ARGS -db $BLAST_DIR/proteins -query "$INPUT_FILE" -out "$BLAST_OUT_DIR/$BASENAME-proteins"
done < "$INPUT_FILES"

rm "$INPUT_FILES"
