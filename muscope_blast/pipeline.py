import argparse
import glob
import gzip
import logging
import os
import re
import subprocess
import sys
import traceback

from Bio import SeqIO


def main():
    logging.basicConfig(level=logging.INFO)
    args = get_args()
    BlastPipeline(**args.__dict__).run()


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-q', '--query', required=True, help='FASTA file to BLAST')
    arg_parser.add_argument('-o', '--out-dir', default='.', help='directory for output files')
    arg_parser.add_argument('-p', '--percent-id', type=Float, default=0.9, help='percentage of the query sequence exactly matching database sequence')
    arg_parser.add_argument('-n', '--num-threads', type=Integer, default=1, help='number of threads to use')
    args = arg_parser.parse_args()
    return args


class BlastPipeline:
    def __init__(self, query, out_dir, percent_id, num_threads):
        self.query = query
        self.out_dir = out_dir
        self.percent_id = percent_id
        self.num_threads = num_threads
