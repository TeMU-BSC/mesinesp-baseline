#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 09:40:48 2020

@author: antonio
"""
import itertools
import os
import time
import json
from utils.app_specific_utils import (format_text_info, store_prediction,
                                      check_surroundings)
from utils.general_utils import Flatten


def detect_annots(datapath, min_upper, annot2code, file2annot_processed,
                  file2annot, annot2label, annot2annot_processed):
    '''
    
    Parameters
    ----------
    datapath : str
        path to folder with text files.
    min_upper : int
        minimum number of character to lowercase a word.
    annot2code : dict
        python dictionary relating every annotation in the input TSV with its
        code.
    file2annot_processed : dict
        DESCRIPTION.
    file2annot : dict
        DESCRIPTION.
    annot2label : dict
        DESCRIPTION.
    annot2annot_processed : dict
        DESCRIPTION.

    Returns
    -------
    total_t : float
        Elapsed time
    final_annotations : dict
        key= string with filename.txt (ex: 'cc_onco837.txt').
        Value = list of annotations (ex: [['Carcinoma microcítico',2690,2711,'MORFOLOGIA_NEOPLASIA','8041/3'],
                                          ['LH', 2618, 2620, '_REJ_MORFOLOGIA_NEOPLASIA', '9650/3']])
    c : int
        number of suggested annotations.

    '''
    start = time.time()
    
    final_annots = {}
    c = 0
    json_object = json.load(open(datapath, 'r'))
    
    for article in json_object['articles']:
        txt = article['abstractText']
        _id = article['id']
        print(article['id'])
        c, final_annots = \
            scan_one_file(txt,_id,file2annot_processed,annot2annot_processed,
                          annot2label,annot2code,file2annot,final_annots,c,min_upper)

    total_t = time.time() - start
    
    return total_t, final_annots, c


def scan_one_file(txt, _id, file2annot_processed, annot2annot_processed, 
                  annot2label, annot2code, file2annot, final_annotations, c, 
                  min_upper=5):
        
    #### 0. Initialize, etc. ####
    new_annots = []
    pos_matrix = []

    #### 2. Format text information ####
    words_final, words_processed2pos = format_text_info(txt, min_upper)

    #### 3. Intersection ####
    # Find words within annotations
    annot_processed_other_files = file2annot_processed.values()

    # Flatten results and get set of it
    annotations_final = set(Flatten(annot_processed_other_files))
    
    # Generate candidates
    words_in_annots = words_final.intersection(annotations_final)

    #### 4. For every token of the intersection, get all original 
    #### annotations associated to it and all matches in text.
    #### Then, check surroundings of all those matches to check if any
    #### of the original annotations is in the text ####
    for match in words_in_annots:

        # Get annotations where this token is present
        original_annotations = [k for k,v in annot2annot_processed.items() \
                                if match in v]

        # Get text locations where this token is present
        match_text_locations = words_processed2pos[match]
         
        # For every original annotation where this token is present:
        for original_annot in original_annotations:
            original_label = annot2label[original_annot]
            original_text_locations = words_processed2pos[match]
            n_chars = len(original_annot)
            n_words = len(original_annot.split())
            
            if len(original_annot.split()) > 1:
                # For every match of the token in text, check its 
                # surroundings and generate predictions
                codes = annot2code[original_annot]
                len_original = len(new_annots)
                for span in match_text_locations:
                    new_annots, pos_matrix = \
                        check_surroundings(txt,span,original_annot,n_chars,
                                           n_words,original_label,new_annots,
                                           pos_matrix,min_upper,codes)
                    if len(new_annots) != len_original:
                        # Stop looking for the same code in more than one place
                        break
                    
            # If original_annotation is just the token, no need to 
            # check the surroundings
            elif len(original_annot.split()) == 1:
                len_original = len(new_annots)
                for span in original_text_locations:
                    # Check span is surrounded by spaces or punctuation signs &
                    # span is not contained in a previously stored prediction
                    if span[0] == 0:
                        cond_a = True
                    else:
                        cond_a = txt[span[0]-1].isalnum() == False
                    if span[1] == len(txt):
                        cond_b = True
                    else:
                        cond_b = txt[span[1]].isalnum() == False

                        
                    if ((cond_a & cond_b) &
                        (not any([(item[0]<=span[0]) & (span[1]<=item[1]) 
                                  for item in pos_matrix]))):
                        
                        # STORE PREDICTION and eliminate old predictions
                        # contained in the new one.
                        codes = annot2code[original_annot]
                        new_annots, pos_matrix = \
                            store_prediction(pos_matrix,new_annots,span[0],
                                             span[1],original_label,
                                             original_annot,txt,codes)
                        if len(new_annots) != len_original:
                            # Stop looking for the same code in more than one 
                            # place
                            break

                
    ## 4. Remove duplicates ##
    new_annots.sort()
    new_annots_no_duplicates = list(k for k,_ in itertools.groupby(new_annots))
    
    ## 5. Check new annotations are not already annotated in their own ann
    '''
    if _id not in file2annot.keys():
        final_new_annots = new_annots_no_duplicates
    else:
        annots_in_ann = file2annot[_id]
        final_new_annots = []
        for new_annot in new_annots_no_duplicates:
            new_annot_word = new_annot[0]
            if any([new_annot_word in x for x in annots_in_ann]) == False:
                final_new_annots.append(new_annot)
    
                
    # Final appends
    c = c + len(final_new_annots)
    final_annotations[_id] = final_new_annots'''
    # Final appends
    c = c + len(new_annots_no_duplicates)
    final_annotations[_id] = new_annots_no_duplicates
    
    return c, final_annotations