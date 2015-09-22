#! /usr/bin/env python
__author__ = 'bendall'

import sys

# Get the version
import pkg_resources
try:
    VERSION = pkg_resources.require("telescope")[0].version
except pkg_resources.DistributionNotFound:
    VERSION = "dev"

# Set the usage string
USAGE   = ''' %(prog)s <command> [<args>]

The most commonly used commands are:
   id       Record changes to the repository
   tag      Add tags to an alignment
'''

from telescope_id import run_telescope_id
from telescope_tag import run_telescope_tag
from telescope_load import run_telescope_load

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Tools for analysis of repetitive DNA elements',
                                     usage=USAGE,
                                     )
    parser.add_argument('--version', action='version', version=VERSION)

    subparsers = parser.add_subparsers(help='sub-command help')

    ''' Parser for ID '''
    id_parser = subparsers.add_parser('id',
                                      description='Reassign reads',
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     )

    inputopts = id_parser.add_argument_group('input', 'Input options')
    inputopts.add_argument('--ali_format', default='sam', help='Alignment Format. Only SAM is supported.')
    inputopts.add_argument('samfile', help='Path to alignment file')
    inputopts.add_argument('gtffile', help='Path to annotation file (GTF format)')
    inputopts.add_argument('--no_feature_key', default='__nofeature__',
                            help='Feature name for unassigned reads. Must not match any other feature name')

    outputopts = id_parser.add_argument_group('output', 'Output options')
    outputopts.add_argument('--verbose', action='store_true',
                            help='Prints verbose text while running')
    outputopts.add_argument('--outdir', default=".",
                             help='Output Directory')
    outputopts.add_argument('--exp_tag', default="telescope",
                            help='Experiment tag')
    #outputopts.add_argument('--min_final_guess', type=float, default=0.01,
    #                        help='Minimum final guess for genome to appear in report. Genomes with one or more final hits will always be included.')
    outputopts.add_argument('--out_matrix', action='store_true',
                            help='Output alignment matrix')
    outputopts.add_argument('--updated_sam', action='store_true', dest='updated_sam',
                            help='Generate an updated alignment file')
    outputopts.add_argument('--checkpoint', action='store_true', dest='checkpoint',
                            help='Enable checkpointing feature')
    outputopts.add_argument('--checkpoint_interval', type=int, default=10,
                            help='Number of EM iterations between checkpoints')
    outputopts.add_argument('--min_prob', type=float, default=0.2,
                            help='Minimum probability to be included in updated alignment file')
    outputopts.add_argument('--conf_prob', type=float, default=0.9,
                            help='Minimum probability for high confidence assignment')


    modelopts = id_parser.add_argument_group('model', 'Model parameters')
    modelopts.add_argument('--piPrior', type=int, default=0,
                           help='Pi Prior equivalent to adding n unique reads')
    modelopts.add_argument('--thetaPrior', type=int, default=0,
                           help='Theta Prior equivalent to adding n non-unique reads')
    #modelopts.add_argument('--score_cutoff', type=float, default=0.01,
    #                       help='Minimum final probability score for alignment')

    emopts = id_parser.add_argument_group('em', 'EM parameters')
    emopts.add_argument('--emEpsilon', type=float, default=1e-7,
                        help='EM Algorithm Epsilon cutoff')
    emopts.add_argument('--maxIter', type=int, default=100,
                        help='EM Algorithm maximum iterations')

    id_parser.set_defaults(func=run_telescope_id)

    ''' Parser for TAG '''
    tag_parser = subparsers.add_parser('tag',
                                       description='Tag BAM file',
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                      )
    tag_parser.add_argument('--verbose', action='store_true',
                            help='Prints verbose text while running')
    tag_parser.add_argument('--gtffile', help='Path to annotation file (GTF format)')
    tag_parser.add_argument('samfile', nargs="?", default="-", help='Path to alignment file (default is STDIN)')
    tag_parser.add_argument('outfile', nargs="?", default="-", help='Output file (default is STDOUT)')

    tag_parser.set_defaults(func=run_telescope_tag)

    ''' Parser for LOAD '''
    load_parser = subparsers.add_parser('load',
                                       description='Load checkpoint file',
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                      )
    load_parser.add_argument('--verbose', action='store_true',
                             help='Prints verbose text while running')
    load_parser.add_argument('--outparam',
                             help='Output this parameter value')
    load_parser.add_argument('--prec', type=int, default=6,
                             help='Output precision')
    load_parser.add_argument('--float', action='store_true',
                             help='Force output as floats')
    load_parser.add_argument('--exp', action='store_true',
                             help='Force output as exponential')
    load_parser.add_argument('checkpoint', help='Checkpoint file')
    load_parser.add_argument('outfile', nargs="?", type=argparse.FileType('w'), default=sys.stdout,
                             help='Output file (default is STDOUT)')


    load_parser.set_defaults(func=run_telescope_load)



    args = parser.parse_args()
    args.func(args)

