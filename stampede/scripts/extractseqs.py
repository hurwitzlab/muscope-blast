#!/usr/bin/env python3
"""
extractseqs.py

This script is part of the muSCOPE-BLAST CyVerse application.

Read a BLAST output file to get sequence hit ids for the reference sequences. Extract the reference
sequences corresponding to each hit from the original reference file(s) and write them to a file.

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

The second column is parsed to extract the reference sample name from the sequence id (e.g. `HOT234_1_0200m`). All
matched sequences are extracted from the reference sample FASTA files and written to a file.
"""

import argparse
import collections
import itertools
import os
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

    # set up file paths
    blast_output_filename_pattern = re.compile(r'(?P<input>.+)-(?P<seq_type>(contigs|genes|proteins))\.tab')
    try:
        blast_input_file_name, seq_type = blast_output_filename_pattern.search(blast_output_fp).groups()
    except Exception as e:
        print('  failed to parse BLAST output file name "{}"'.format(blast_output_fp))
        raise e

    blast_input_base_name = os.path.basename(blast_input_file_name)
    seq_type_ext = {'contigs': '.fa', 'genes': '.fna', 'proteins': '.faa'}
    blast_ref_sample_fasta_file_template = os.path.join(
        ohana_sequence_dp,
        '{refsample}',
        seq_type + seq_type_ext[seq_type]
    )
    output_file_path_template = os.path.join(
        ohana_hit_output_dp,
        blast_input_base_name + '-{refsample}-' + seq_type + seq_type_ext[seq_type]
    )

    # parse the BLAST output file
    with open(blast_output_fp, 'rt') as blast_output_file:
        blast_refdb_hits = get_blast_reference_hits(blast_output_file=blast_output_file, blast_output_row_limit=blast_hit_limit)
    print('finished parsing BLAST output file "{}"'.format(blast_output_fp))

    # find each hit from the BLAST output in the corresponding BLAST reference sample FASTA files
    # and copy the sequence to a file
    for blast_ref_sample_name, sample_sequence_ids in sorted(blast_refdb_hits.items()):
        blast_ref_sample_fasta_fp = blast_ref_sample_fasta_file_template.format(refsample=blast_ref_sample_name)
        if not os.path.exists(blast_ref_sample_fasta_fp):
            print('ERROR: BLAST reference "{}" does not exist'.format(blast_ref_sample_fasta_fp))
        else:
            print('extracting sequence hits from "{}"'.format(blast_ref_sample_fasta_fp))
            output_fp = output_file_path_template.format(refsample=blast_ref_sample_name)
            with open(blast_ref_sample_fasta_fp, 'rt') as sample_fasta_file, \
                    open(output_fp, 'wt') as sample_sequence_output_file:

                for i, seq in enumerate(find_sequences(sample_sequence_ids, sample_fasta_file)):
                    SeqIO.write(seq, sample_sequence_output_file, 'fasta')

                print('wrote {} sequence(s) to file "{}"'.format(i+1, output_fp))


def find_sequences(sequence_ids, fasta_file):
    """Search fasta_file for sequence ids in sequence_ids and write the corresponding sequence and yield each
    sequence record that is found.

    :param sequence_ids: (set of str)
    :param fasta_file: (file-like object)
    :yield: (biopython sequence object)
    """
    remaining_sequence_ids = set(sequence_ids)
    for seq in SeqIO.parse(fasta_file, 'fasta'):
        if seq.id in remaining_sequence_ids:
            remaining_sequence_ids.remove(seq.id)
            yield seq

            if len(remaining_sequence_ids) == 0:
                break
    return


def get_blast_reference_hits(blast_output_file, blast_output_row_limit):
    """Read the specified BLAST output file to build a dictionary with Ohana reference database names as keys and
    sets of sequence ids as values.

    BLAST output files look like this:
        A HOT234_1_0200m_rep_c55158_2   100.00  147 0   0   1   147 400 546 2e-70    272
        A HOT234_1_0200m_c10096_4       100.00  147 0   0   1   147 400 546 2e-70    272
        A HOT238_1c_0200m_c3_1          100.00  147 0   0   1   147 1   147 2e-70    272
        A HOT238_1c_0200m_rep_c260499_1 100.00  147 0   0   1   147 400 546 2e-70    272

    The dictionary generated by this function looks like this:
        {
            'HOT234_1_0200m': {'HOT234_1_0200m_rep_c55158_2', 'HOT234_1_0200m_c10096_4'},
            'HOT238_1c_0200m': {'HOT238_1c_0200m_c3_1', 'HOT238_1c_0200m_rep_c260499_1'}
        }

    :param blast_output_file: (file-like object) BLAST output file
    :param blast_output_row_limit: (int) maximum number of BLAST output rows to process, None to process all rows
    :return: dictionary of Ohana reference database names mapped to sets of sequence ids
    """
    blast_db_hits = collections.defaultdict(set)

    sample_sequence_pattern = re.compile(r'^(?P<sample_id>HOT\d+_(\d*c?_)?\d+m)')
    for i, blast_output_row in enumerate(itertools.islice(blast_output_file, blast_output_row_limit)):
        print(blast_output_row)
        try:
            _, sample_sequence, _ = blast_output_row.strip().split('\t', maxsplit=2)
            sample_id = sample_sequence_pattern.match(sample_sequence).group('sample_id')
            blast_db_hits[sample_id].add(sample_sequence)
        except Exception as e:
            print('failed to parse row {}: "{}"'.format(i+1, blast_output_row))
            raise e

    row_count = sum([len(sequences) for sequences in blast_db_hits.values()])
    print('finished parsing {} rows of BLAST output'.format(row_count))

    return blast_db_hits


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
    #test_blast_output_dp = '/home/jklynch/host/project/muscope/apps/test-blast-output/test.fa-proteins.tab'
    #test_blast_db_fasta_dp = '/home/jklynch/host/project/muscope/ohana/'
    #test_sequence_output_dp = '/home/jklynch/host/project/muscope/apps/test-sequence-output/'
    args = get_args()
    main(**args.__dict__)
