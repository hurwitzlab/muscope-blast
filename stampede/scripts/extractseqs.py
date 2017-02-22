#!/usr/bin/env python3
"""
extractseqs.py

This script is part of the muSCOPE-BLAST CyVerse application.

Read a BLAST output file to get sequence hit ids for the reference sequences. Extract the reference
sequences corresponding to each hit and write them to a file.

The muSCOPE-BLAST application generates BLAST output files with names like
     + test.fa-contigs.tab
     + test.fa-genes.tab
     + test.fa-proteins.tab
where 'test.fa' is the name of the input file to BLAST and contigs, genes and proteins are the Ohana reference
databases.

Each .tab file looks like this:
    A HOT234_1_0200m_rep_c55158_2 100.00  147 0   0   1   147 400 546 2e-70    272
    A HOT229_1_0200m_c10096_4 100.00  147 0   0   1   147 400 546 2e-70    272
    A HOT233_1c_0200m_c3_1    100.00  147 0   0   1   147 1   147 2e-70    272
    A HOT238_1c_0200m_rep_c260499_1   100.00  147 0   0   1   147 400 546 2e-70    272
    A HOT236_1_0200m_c24599_1 100.00  147 0   0   1   147 358 504 2e-70    272

The second column is parsed to extract the reference sample name (e.g. `HOT234_1_0200m`) and the reference
sequence id (e.g. `rep_c55158_2`). All matched sequences are extracted from the reference sample FASTA files and
written to a file.
"""

import argparse
import collections
import itertools
import os
import pprint
import re

from Bio import SeqIO


def main(blast_output_fp, ohana_sequence_dp, ohana_hit_output_dp, blast_hit_limit):
    """Extract sequences corresponding to BLAST hits.

    :param blast_output_fp: (str) file path to a BLAST output file
    :param ohana_sequence_dp: (str) directory path to Ohana BLAST reference fasta files
    :param ohana_hit_output_dp: (str) directory path for sequence file output
    :param blast_hit_limit: (int) maximum number of BLAST hits to process, None for all hits
    :return:
    """

    if not os.path.isfile(blast_output_fp):
        print('BLAST output file "{}" does not exist.'.format(blast_output_fp))
        exit(1)
    if not os.path.isdir(ohana_sequence_dp):
        print('BLAST database directory "{}" does not exist.'.format(ohana_sequence_dp))
        exit(1)
    if not os.path.isdir(ohana_hit_output_dp):
        print('Sequence output directory "{}" will be created.'.format(ohana_hit_output_dp))
        os.makedirs(ohana_hit_output_dp, exist_ok=True)

    # parse the BLAST output file
    with open(blast_output_fp, 'rt') as blast_output_file:
        blast_refdb_hits = get_blast_reference_hits(blast_output_file=blast_output_file, blast_hit_limit=blast_hit_limit)
    print('finished parsing BLAST output file "{}"'.format(blast_output_fp))

    # set up file paths
    blast_input_file_name, seq_type = parse_blast_output_file_path(blast_output_fp)
    blast_input_base_name = os.path.basename(blast_input_file_name)
    seq_type_ext = {'contigs': '.fa', 'genes': '.fna', 'proteins': '.faa'}
    blast_ref_sample_fasta_file_pattern = os.path.join(
        ohana_sequence_dp,
        '{refsample}',
        seq_type + seq_type_ext[seq_type]
    )
    output_file_pattern = os.path.join(
        ohana_hit_output_dp,
        blast_input_base_name + '-{refsample}-' + seq_type + seq_type_ext[seq_type]
    )

    # find each hit from the BLAST output in the corresponding BLAST reference sample FASTA files
    # and copy the sequence to a file
    for blast_ref_sample_name, matched_sequence_ids in sorted(blast_refdb_hits.items()):
        blast_ref_sample_fasta_fp = blast_ref_sample_fasta_file_pattern.format(refsample=blast_ref_sample_name)
        if not os.path.exists(blast_ref_sample_fasta_fp):
            print('ERROR: BLAST database "{}" does not exist'.format(blast_ref_sample_fasta_fp))
        else:
            output_fp = output_file_pattern.format(refsample=blast_ref_sample_name)
            print('extracting sequence hits from "{}"'.format(blast_ref_sample_fasta_fp))
            with open(blast_ref_sample_fasta_fp, 'rt') as blast_ref_sample_fasta_file, \
                    open(output_fp, 'wt') as ref_sample_sequence_output_file:
                write_sequence_hits(matched_sequence_ids, blast_ref_sample_fasta_file, ref_sample_sequence_output_file)


def parse_blast_output_file_path(fp):
    """Parse input file name and sequence type (contigs, genes, proteins) from a file path.

    Valid file names look like this:
        test.fa-contigs.tab
        test.fa-genes.tab
        test.fa-proteins.tab

    The input file name for the examples above is 'test.fa'. The sequence types are 'contigs', 'genes' and
    'proteins' respectively.

    :param fp: (str) file path or file name
    :return: 2-ple of strs (input file name, sequence type)
    """
    blast_output_filename_pattern = re.compile(r'(?P<input>.+)-(?P<seq_type>(contigs|genes|proteins))\.tab')
    m = blast_output_filename_pattern.search(fp)
    if m is None:
        print('  failed to parse "{}"'.format(fp))
        return None, None
    else:
        return m.group('input'), m.group('seq_type')


def write_sequence_hits(matched_sequence_ids, blast_db_fasta_file, output_file):
    """Search blast_db_fasta_file for sequence ids in matched_sequence_ids and write the corresponding sequence
    to output_file.

    :param matched_sequence_ids: (set of str)
    :param blast_db_fasta_file: (file-like object)
    :param output_file: (file-like object)
    :return: no return value
    """
    blast_hit_id_search_set = set(matched_sequence_ids)
    for seq in SeqIO.parse(blast_db_fasta_file, 'fasta'):
        if seq.id in blast_hit_id_search_set:
            # print(seq)
            SeqIO.write(seq, output_file, 'fasta')
            blast_hit_id_search_set.remove(seq.id)

            if len(blast_hit_id_search_set) == 0:
                break
    for seq_id in blast_hit_id_search_set:
                print('  ERROR: failed to find "{}"'.format(seq_id))


def get_blast_reference_hits(blast_output_file, blast_hit_limit):
    """Read the specified BLAST output file to build a dictionary with Ohana reference database names as keys and
    sets of sequence ids as values.

    BLAST output files look like this:
        A HOT234_1_0200m_rep_c55158_2   100.00  147 0   0   1   147 400 546 2e-70    272
        A HOT234_1_0200m_c10096_4       100.00  147 0   0   1   147 400 546 2e-70    272
        A HOT238_1c_0200m_c3_1          100.00  147 0   0   1   147 1   147 2e-70    272
        A HOT238_1c_0200m_rep_c260499_1 100.00  147 0   0   1   147 400 546 2e-70    272

    The dictionary generated by this function looks like this:
        {
            'HOT234_1_0200m': {'rep_c55158_2', 'c10096_4'},
            'HOT238_1c_0200m': {'c3_1', 'rep_c260499_1'}
        }

    :param blast_output_file: (file-like object) BLAST output file
    :param blast_hit_limit: (int) maximum number of BLAST hits to process, None to process all hits
    :return: dictionary of Ohana reference database names mapped to sets of sequence ids
    """
    blast_db_hits = collections.defaultdict(set)

    for blast_hit_id, ohana_blast_db, seq_id \
            in itertools.islice(extract_blast_db_and_sequence_id(blast_output_file), blast_hit_limit):
        blast_db_hits[ohana_blast_db].add(seq_id)

    pprint.pprint(blast_db_hits)
    return blast_db_hits


def extract_blast_db_and_sequence_id(blast_output_file):
    """Parse and yield tuples of (sample name, sequence id) from each line of the blast_output_file.

    :param blast_output_file: (file-like object)
    :return: (sample name, sequence id)
    """
    p = re.compile(r'(?P<db>HOT\d+(_\dc?)?_\d+m)_(?P<seq_id>(rep_)?c\d+(_\d)?)')
    for i, line in enumerate(blast_output_file):
        row_values = line.strip().split('\t')
        s = row_values[1]
        m = p.match(s)
        if m is None:
            raise Exception('failed to parse line {}: "{}"'.format(i, line))
        else:
            yield s, m.group('db'), m.group('seq_id')
    print('finished parsing {} rows of BLAST output'.format(i+1))


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('blast_output_fp', metavar='FILE', help='file of BLAST hits')
    arg_parser.add_argument('ohana_sequence_dp', metavar='DIR', help='directory of Ohana contigs, genes, proteins')
    arg_parser.add_argument('ohana_hit_output_dp', metavar='DIR', help='directory for Ohana BLAST hit output')
    arg_parser.add_argument(
        '-l', '--blast-hit-limit', type=int, default=None,  help='extract only the first <blast-hit-limit> BLAST hits')
    args = arg_parser.parse_args()
    print(args)
    return args


if __name__ == '__main__':
    #test_blast_output_dp = '/home/jklynch/host/project/muscope/apps/test-blast-output/'
    #test_blast_db_fasta_dp = '/home/jklynch/host/project/muscope/ohana/'
    #test_sequence_output_dp = '/home/jklynch/host/project/muscope/apps/test-sequence_output/'
    args = get_args()
    main(**args.__dict__)
