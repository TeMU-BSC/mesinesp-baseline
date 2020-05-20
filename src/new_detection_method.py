#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 15:45:05 2019

@author: antonio
OUTPUT_TSV
"""

import os
from utils.app_specific_utils import (format_input_info, parse_tsv)
from utils.general_utils import argparser   
from detect_annotations import detect_annots
import json


if __name__ == '__main__':
    
    min_upper = 5 # minimum number of characters a string must have to lowercase it

    ######## Define paths ########   
    print('\n\nParsing script arguments...\n\n')
    datapath, tsv_path, out_path = argparser()
    
    ######## GET ANN INFORMATION ########    
    # Get DataFrame
    print('\n\nObtaining original annotations...\n\n')
    df_annot = parse_tsv(tsv_path)
    
    ######## FORMAT ANN INFORMATION #########
    print('\n\nFormatting original annotations...\n\n')
    (file2annot, file2annot_processed, annot2label, 
     annot2annot_processed, annot2code) = format_input_info(df_annot, min_upper)
    
    ######## FIND MATCHES IN TEXT ########
    print('\n\nFinding new annotations...\n\n')
    time_, final_annotations, c = detect_annots(datapath, min_upper, annot2code,
                                                file2annot_processed, file2annot,
                                                annot2label, annot2annot_processed)
    
    print('Elapsed time: {}s'.format(round(time_, 3)))
    print('Number of suggested annotations: {}'.format(c))
           
    ######### WRITE OUTPUT ###########
    # Store only codes
    for k,v in final_annotations.items():
        final_annotations[k] = list(set(map(lambda x: x[-1], v)))
        
    # Write output
    json_array = []
    for k, v in final_annotations.items():
        json_array.append({'id': k, 'labels': v})
    out = {}
    out['documents'] = json_array
    
    with open(os.path.join(out_path, 'output_file.json'), 'w') as my_file:
        json.dump(out, my_file)
    
    print('\n\nFINISHED!')
