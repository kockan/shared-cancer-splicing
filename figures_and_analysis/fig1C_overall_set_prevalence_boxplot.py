#!/usr/bin/env python3

"""
fig1C_overall_set_prevalence_boxplot.py

Python 3 code for plotting prevalences of tissue-matched, core normal, and
other junctions from TCGA samples.

"""

import argparse
from datetime import datetime
import glob
import logging
from matplotlib import use; use('pdf')
import os
import pandas as pd
from scipy import stats
import sys
try:
    from utilities.utilities import _TCGA_ABBR, _PER
except ModuleNotFoundError:
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    )
    from utilities.utilities import _TCGA_ABBR, _PER
from utilities.utilities import grouped_boxplots_with_table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plot cancer-type prevalence boxplot for overall sets.'
    )
    parser.add_argument(
        '--set-memberships', '-s',
        help='Give the directory containing set membership files for all TCGA '
             'cancer types.'
    )
    parser.add_argument(
        '--output-path', '-o', default='./',
        help='give path for output log file and figure'
    )
    parser.add_argument(
        '--log-level', '-l', default='INFO', choices=['INFO'],
        help='choose what logging mode to run (only INFO currently supported)'
    )

    args = parser.parse_args()
    set_dir = args.set_memberships
    out_path = args.output_path
    log_mode = args.log_level

    now = datetime.now().strftime('%m-%d-%Y_%H.%M.%S')
    log_file = os.path.join(
        out_path, 'fig1C_overall_set_prevalence_boxplot_log_{}.txt'.format(now)
    )
    logging.basicConfig(filename=log_file, level=log_mode)
    logging.info('input is: {}'.format(' '.join(sys.argv)))

    data_label_dict = {}
    grouped_data_dict = {
        'pan cancer': {
            'data': [[], [], []], 'table_data': [0, 0, 0]
        }
    }
    gtex_for_stats = []
    non_gtex_for_stats = []
    for cancer, abbr in _TCGA_ABBR.items():
        per_col = cancer + _PER
        logging.info(cancer)
        jx_path = os.path.join(
            set_dir, '{}_piechart_annotation*.csv'.format(cancer)
        )
        jx_file = glob.glob(jx_path)[0]
        max_chunk = 1e6
        jx_df = pd.DataFrame()
        chunks = pd.read_table(jx_file, sep=',', chunksize=max_chunk)
        for chunk in chunks:
            chunk = chunk.fillna(0)
            chunk = chunk[chunk[per_col] >= 0.01]
            jx_df = pd.concat([jx_df, chunk])

        in_paired = jx_df[jx_df['paired'] == 1][per_col].tolist()
        in_gtex = jx_df[
            (jx_df['gtex'] == 1) & (jx_df['paired'] == 0)
        ][per_col].tolist()
        non_gtex = jx_df[jx_df['gtex'] == 0][per_col].tolist()

        grouped_data_dict['pan cancer']['data'][0].extend(in_paired)
        grouped_data_dict['pan cancer']['data'][1].extend(in_gtex)
        grouped_data_dict['pan cancer']['data'][2].extend(non_gtex)

        grouped_data_dict['pan cancer']['table_data'][0] += len(in_paired)
        grouped_data_dict['pan cancer']['table_data'][1] += len(in_gtex)
        grouped_data_dict['pan cancer']['table_data'][2] += len(non_gtex)

        gtex_for_stats.extend(in_paired)
        gtex_for_stats.extend(in_gtex)
        non_gtex_for_stats.extend(non_gtex)

    stat, pval = stats.kruskal(
        gtex_for_stats, non_gtex_for_stats
    )
    logging.info("kruskal statistic: {}".format(stat))
    logging.info("kruskal p-value: {}".format(pval))

    plot_info_dict = {}
    plot_info_dict['light colors'] = [
        'xkcd:bright sky blue', 'xkcd:kermit green', 'xkcd:saffron'
    ]

    plot_info_dict['dark colors'] = plot_info_dict['light colors']
    plot_info_dict['legend'] = [
        'tissue-matched\nnormal junctions', 'core normal\njunctions',
        'other junctions'
    ]
    plot_info_dict['row colors'] = plot_info_dict['light colors']
    plot_info_dict['row font color'] = ['black', 'black', 'black']
    plot_info_dict['row labels'] = plot_info_dict['legend']
    fig_name = 'fig1C_alltcga_set_prevalence_boxplot_{}.pdf'.format(now)
    fig_file = os.path.join(out_path, fig_name)
    logging.info('saving figure at {}'.format(fig_file))
    grouped_boxplots_with_table(grouped_data_dict, plot_info_dict, fig_file)
