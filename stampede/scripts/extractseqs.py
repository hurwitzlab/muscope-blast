# Demonstrate how to take sequence identifiers from BLAST output files
#     + test.fa-contigs.tab
#     + test.fa-genes.tab
#     + test.fa-proteins.tab
# where 'test.fa' is the name of the input file to BLAST.
# 
# Each .tab file looks like this:
# 
# ```
# A	HOT234_1_0200m_rep_c55158_2	100.00	147	0	0	1	147	400	546	2e-70	 272
# A	HOT229_1_0200m_c10096_4	100.00	147	0	0	1	147	400	546	2e-70	 272
# A	HOT233_1c_0200m_c3_1	100.00	147	0	0	1	147	1	147	2e-70	 272
# A	HOT238_1c_0200m_rep_c260499_1	100.00	147	0	0	1	147	400	546	2e-70	 272
# A	HOT236_1_0200m_c24599_1	100.00	147	0	0	1	147	358	504	2e-70	 272
# ```
# 
# The second column should be parsed to extract the source file (e.g. `HOT234_1_0200m`) and the matched
# sequence id (e.g. `rep_c55158_2`). All matched sequences should be extracted from each source file and
#  written to a file.

import argparse
import collections
import itertools
import os
import pprint
import re

from Bio import SeqIO


def extract_blast_db_and_sequence_id(blast_output_file):
    p = re.compile(r'(?P<db>HOT\d+(_\dc?)?_\d+m)_(?P<seq_id>(rep_)?c\d+(_\d)?)')
    for i, line in enumerate(blast_output_file):
        row_values = line.strip().split('\t')
        #print(line)
        #print(row_values)
        s = row_values[1]
        print('parsing "{}"'.format(s))
        m = p.match(s)
        if m is None:
            raise Exception()
        else:
            yield m.group('db'), m.group('seq_id')
    print('finished parsing {} rows of BLAST output'.format(i+1))


def get_blast_output_file_paths(blast_output_dp):
    blast_output_filename_pattern = re.compile(r'(?P<input>.+)-(?P<seq_type>(contigs|genes|proteins))\.tab')
    for root, dirnames, filenames in os.walk(top=blast_output_dp):
        print(root)
        for filename in filenames:
            print(filename)
            m = blast_output_filename_pattern.search(filename)
            if m is None:
                print('  failed to parse filename "{}"'.format(filename))
            else:
                #print('  input: "{}"'.format(m.group('input')))
                #print('  sequence type: "{}"'.format(m.group('seq_type')))
            
                blast_output_fp = os.path.join(root, filename)
                yield m.group('input'), m.group('seq_type'), blast_output_fp
    

def extract_matching_sequences(blast_output_dp, ohana_sequence_dp, ohana_hit_output_dp):
    """Parse each .tab file in blast_output_dp to find matched sequence ids, then extract matched
    sequences from the blast_db_fasta_dp. Write extracted sequences to sequence_output_dp.
    
    Build an intermediate dictionary that looks like this:
    {
        'contigs': {
            'HOT229_1_0200m': ['c10096'],
            'HOT233_1c_0200m': ['c3'],
            'HOT234_1_0200m': ['rep_c55158']
        },
        'genes': {
            'HOT229_1_0200m': ['c10096_4'],
            'HOT233_1c_0200m': ['c3_1'],
            'HOT234_1_0200m': ['rep_c55158_2']
        },
        'proteins': {
            'HOT233_1_0770m': ['c3_1'],
            'HOT233_1c_0200m': ['c3_1'],
            'HOT236_1_0200m': ['c24599_1']
        }
    }

    :param blast_output_dp: (str) path to BLAST output directory
    :param ohana_sequence_dp: (str) path to directory of BLAST database fasta files (Ohana catalog)
    :param ohana_hit_output_dp: (str) path to directory for matching sequence output
    """
    if not os.path.isdir(blast_output_dp):
        print('BLAST output directory "{}" does not exist.'.format(blast_output_dp))
        exit(1)
    if not os.path.isdir(ohana_sequence_dp):
        print('BLAST database directory "{}" does not exist.'.format(ohana_sequence_dp))
        exit(1)
    if not os.path.isdir(ohana_hit_output_dp):
        print('Sequence output directory "{}" will be created.'.format(ohana_hit_output_dp))
        os.makedirs(ohana_hit_output_dp, exist_ok=True)

    def default_dict_set_factory():
        return collections.defaultdict(set)
    blast_db_hits = collections.defaultdict(default_dict_set_factory)

    for blast_input_file_name, seq_type, blast_output_fp in get_blast_output_file_paths(blast_output_dp):
        # blast_input_file_name is a user-supplied file that was BLASTed against the Ohana catalog
        print('BLAST input file name: "{}"'.format(blast_input_file_name))
        print('sequence type: {}'.format(seq_type))
        print('BLAST output file path: "{}"'.format(blast_output_fp))

        seq_type_blast_hits = blast_db_hits[seq_type]
        
        with open(blast_output_fp, 'rt') as blast_output_file:
            for ohana_blast_db, seq_id in itertools.islice(extract_blast_db_and_sequence_id(blast_output_file), 3):
                seq_type_blast_hits[ohana_blast_db].add(seq_id)
                print('  Ohana BLAST db: "{}"'.format(ohana_blast_db))
                print('  sequence id: "{}"'.format(seq_id))

        print('finished parsing BLAST output file "{}"'.format(blast_output_fp))

    # now use blast_db_hits to extract the matched sequences from the BLAST input files
    pprint.pprint(blast_db_hits)

    seq_type_ext = {'contigs': '.fa', 'genes': '.fna', 'proteins': '.faa'}
    for seq_type, seq_type_blast_hits in blast_db_hits.items():
        print('extracting sequences of type "{}"'.format(seq_type))
        for blast_db_name, matched_sequence_ids in sorted(seq_type_blast_hits.items()):
            blast_db_fasta_fp = os.path.join(ohana_sequence_dp, blast_db_name, seq_type + seq_type_ext[seq_type])

            if not os.path.exists(blast_db_fasta_fp):
                print('ERROR: "{}" does not exist'.format(blast_db_fasta_fp))
            else:
                print('extracting "{}" sequence hits from "{}"'.format(seq_type, blast_db_fasta_fp))
                output_fp = os.path.join(ohana_hit_output_dp, blast_db_name + '-' + seq_type + seq_type_ext[seq_type])
                with open(blast_db_fasta_fp, 'rt') as blast_db_file, open(output_fp, 'wt') as output_file:
                    seq_id_search_set = set(matched_sequence_ids)
                    for seq in SeqIO.parse(blast_db_file, 'fasta'):
                        if seq.id in seq_id_search_set:
                            #print(seq)
                            SeqIO.write(seq, output_file, 'fasta')
                            seq_id_search_set.remove(seq.id)

                            if len(seq_id_search_set) == 0:
                                break
                for seq_id in seq_id_search_set:
                    print('  ERROR: failed to find "{}"'.format(seq_id))
            #for matched_sequence_id in matched_sequence_ids:
            #    print('  extracting sequence id "{}"'.format(matched_sequence_id))
        

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('blast_output_dp', help='directory of BLAST hits files')
    arg_parser.add_argument('ohana_sequence_dp', help='directory of Ohana contigs, genes, proteins')
    arg_parser.add_argument('ohana_hit_output_dp', help='directory for Ohana BLAST hit output')
    args = arg_parser.parse_args()
    print(args)

    #test_blast_output_dp = '/home/jklynch/host/project/muscope/apps/test-blast-output/'
    #test_blast_db_fasta_dp = '/home/jklynch/host/project/muscope/ohana/'
    #test_sequence_output_dp = '/home/jklynch/host/project/muscope/apps/test-sequence_output/'
    extract_matching_sequences(**args.__dict__)
