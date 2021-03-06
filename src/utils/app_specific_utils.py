#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 18:24:28 2020

@author: antonio
OUTPUT_TSV
"""

import pandas as pd
import string
from spacy.lang.es import STOP_WORDS
from utils.general_utils import remove_accents, adjacent_combs, strip_punct, normalize_str, tokenize
import re


def tokenize_span(text, n_words):
    '''
    DESCRIPTION: obtain all token combinations in a text and information 
    about the position of every token combination in the original text.
    
    Parameters
    ----------
    text: string
    n_words: int 
        It is the maximum number of tokens I want in a token combination.

    Returns
    -------
    token_span2id: python dict 
        It relates every token combination with an ID.
    id2token_span_pos: python dict
        It relates every token combination (identified by an ID) with its 
        position in the text.
    token_spans: list
        list of token combinations
    '''
    
    # Split text into tokens (words), obtain their position and the previous token.
    tokens2pos = {}
    m_last = ''
    for m in re.finditer(r'\S+', text):
        if all([i in string.punctuation for i in m.group()])==False:
            exit_bool = 0
            
            # remove final and initial punctuation
            m_end, m_start, m_group, exit_bool = strip_punct(m.end(), m.start(),
                                                             m.group(), exit_bool)
                
            # fill dictionary
            if m_group in tokens2pos.keys():
                tokens2pos[m_group].append([m_start, m_end, m_last])
            else:
                tokens2pos[m_group] = [[m_start, m_end, m_last]]
            m_last = m_group
        
    # Obtain token combinations
    id2token_span, id2token_span_pos, token_spans = adjacent_combs(text, 
                                                                   tokens2pos,
                                                                   n_words)
    
    # Reverse dict (no problem, keys and values are unique)
    token_span2id = {' '.join(v): k for k, v in id2token_span.items()}
    
    return token_span2id, id2token_span_pos, token_spans
    
def normalize_tokens(token_spans, min_upper):
    '''
    DESCRIPTION: normalize tokens: lowercase, remove extra whitespaces, 
    remove punctuation and remove accents.
    
    Parameters
    ----------
    token_spans: list
    min_upper: int. S
        It specifies the minimum number of characters of a word to lowercase
        it (to prevent mistakes with acronyms).

    Returns
    -------
    token_span_processed2token_span: python dict 
        It relates the normalized token combinations with the original unnormalized ones.
    '''
    token_span2token_span = dict(zip(token_spans, token_spans))
    
    # Lowercase
    token_span_lower2token_span = dict((k.lower(), v) if len(k) > min_upper else 
                                       (k,v) for k,v in token_span2token_span.items())

    # Remove whitespaces
    token_span_bs2token_span = dict((re.sub('\s+', ' ', k).strip(), v) for k,v 
                                    in token_span_lower2token_span.items())

    # Remove punctuation
    token_span_punc2token_span = dict((k.translate(str.maketrans('', '', string.punctuation)), v) for k,v in token_span_bs2token_span.items())
    
    # Remove accents
    token_span_processed2token_span = dict((remove_accents(k), v) for k,v in token_span_punc2token_span.items())
    
    return token_span_processed2token_span


def parse_tsv(input_path):
    '''
    DESCRIPTION: Get information from ann that was already stored in a TSV file.
    
    Parameters
    ----------
    input_path: string
        path to TSV file with columns: ['annotator', 'bunch', 'filename', 
        'mark','label', 'offset1', 'offset2', 'span', 'code']
        Additionally, we can also have the path to a 3 column TSV: ['code', 'label', 'span']
    
    Returns
    -------
    df_annot: pandas DataFrame
        It has 4 columns: 'filename', 'label', 'code', 'span'.
    '''
    df_annot = pd.read_csv(input_path, sep='\t', header=0)
    if len(df_annot.columns) == 8:
        df_annot.columns=['annotator', 'bunch', 'filename', 'mark',
                      'label', 'offset1', 'offset2', 'span', 'code']
    else:
        df_annot.columns = ['code', 'span']
        #df_annot['label'] = 'MORFOLOGIA_NEOPLASIA'
        df_annot['filename']  ='xx'
        df_annot['label'] = 'DeCS'
    return df_annot

def format_input_info(df_annot, min_upper):
    '''
    DESCRIPTION: Build useful Python dicts from DataFrame with info from TSV file
    
    Parameters
    ----------
    df_annot: pandas DataFrame 
        With 4 columns: 'filename', 'label', 'code', 'span'
    min_upper: int. 
        It specifies the minimum number of characters of a word to lowercase 
        it (to prevent mistakes with acronyms).
    
    Returns
    -------
    file2annot: python dict
    file2annot_processed: python dict
    annot2label: python dict
        It has every unmodified annotation and its label.
    annot2annot_processed: python dict 
        It has every unmodified annotation and the words it has normalized.
    '''
    # Build useful Python dicts from DataFrame with info from .ann files
    file2annot = {}
    file2annot['xx'] = df_annot.span.tolist()
    '''for filename in list(df_annot.filename):
        file2annot[filename] = list(df_annot[df_annot['filename'] == filename].span)'''
        
    set_annotations = set(df_annot.span)
    
    annot2label = dict(zip(df_annot.span,df_annot.label))
    
    annot2code = df_annot.groupby('span')['code'].apply(lambda x: x.tolist()).to_dict()
    
    annot2annot = dict(zip(set_annotations, set_annotations))
    
    # Split values: {'one': 'three two'} must be {'one': ['three', 'two']}   
    annot2annot_split = annot2annot.copy()
    annot2annot_split = dict((k, v.split(' ')) for k,v in annot2annot_split.items())
    #annot2annot_split = dict((k, tokenize(v)) for k,v in annot2annot_split.items())
    
    # Do not store stopwords or single-character words as values
    for k, v in annot2annot_split.items():
        annot2annot_split[k] = list(filter(lambda x: x not in STOP_WORDS, v))
    for k, v in annot2annot_split.items():
        annot2annot_split[k] = list(filter(lambda x: len(x) > 1, v))
    
    # Trim punctuation or multiple spaces
    annot2annot_trim = annot2annot.copy()
    for k, v in annot2annot_split.items():
        annot2annot_trim[k] = list(map(lambda x: x.strip(string.punctuation + ' '), v))
        
    # Lower case values
    annot2annot_lower = annot2annot_trim.copy()
    for k, v in annot2annot_trim.items():
        annot2annot_lower[k] = list(map(lambda x: x.lower() if len(x) > min_upper else x, v))
    
    # remove accents from annotations
    annot2annot_processed = annot2annot_lower.copy()
    for k, v in annot2annot_lower.items():
        annot2annot_processed[k] = list(map(lambda x: remove_accents(x), v))
    
    # file2unaccented annotations
    file2annot_processed = {}
    for (k,v) in file2annot.items():
        aux = list(map(lambda x:annot2annot_processed[x], v))
        file2annot_processed[k] = aux

    return file2annot, file2annot_processed, annot2label, annot2annot_processed, annot2code


def format_text_info(txt, min_upper):
    '''
    DESCRIPTION: 
    1. Obtain list of words of interest in text (no STPW and longer than 1 character)
    2. Obtain dictionary with words of interest and their position in the 
    original text. Words of interest are normalized: lowercased and removed 
    accents.
    
    Parameters
    ----------
    txt: str 
        contains the text to format.
    min_upper: int. 
        Specifies the minimum number of characters of a word to lowercase it
        (to prevent mistakes with acronyms).
    
    Returns
    -------
    words_processed2pos: dictionary
        It relates the word normalzied (trimmed, removed stpw, lowercased, 
        removed accents) and its position in the original text.
    words_final: set
            set of words in text.
    '''
    
    # Get individual words and their position in original txt
    words = tokenize(txt)
    #print(words)
    
    # Remove beginning and end punctuation and whitespaces. 
    words_no_punctuation = list(map(lambda x: x.strip(string.punctuation + ' '), words))
    #print(words_no_punctuation)
    
    # Remove stopwords and single-character words
    large_words = list(filter(lambda x: len(x) > 1, words_no_punctuation))
    #print(large_words)
    words_no_stw = set(filter(lambda x: x.lower() not in STOP_WORDS, large_words))
    #print(words_no_stw)
    # Create dict with words and their positions in text
    words2pos = {}
    for word in words_no_stw:
        occurrences = list(re.finditer(re.escape(word), txt))
        if len(occurrences) == 0:
            print('ERROR: ORIGINAL WORD NOT FOUND IN ORIGINAL TEXT')
            print(word)
        pos = list(map(lambda x: x.span(), occurrences))
        words2pos[word] = pos
        
    #print(words2pos)
    
    # Dictionary relating original words with words processed
    words2words = dict(zip(words_no_stw, words_no_stw))
    words2words_processed = dict((k, remove_accents(k.lower())) if len(k) > min_upper else 
                                (k,v) for k,v in words2words.items())
    # Map original position to processed word
    words_processed2pos = {}
    for k, v in words2pos.items():
        k_processed = words2words_processed[k]
        if k_processed not in words_processed2pos:
            words_processed2pos[k_processed] = v
        else:
            words_processed2pos[k_processed] = words_processed2pos[k_processed] + v
    
    '''# lowercase words and remove accents from words -> HERE I LOSE INFORMATION!
    # If I have 'Sarcoma' and 'sarcoma', only one of the two of them is kept
    words_processed2pos = dict((remove_accents(k.lower()), v) if len(k) > min_upper else 
                                (k,v) for k,v in words2pos.items())'''
    
    # Set of transformed words
    words_final = set(words_processed2pos)
    
    return words_final, words_processed2pos

def store_prediction(pos_matrix, predictions, off0, off1, original_label, 
                     original_annot, txt, codes):
                                        
    # 1. Eliminate old annotations if the new one contains them
    (pos_matrix, 
     predictions) = eliminate_contained_annots(pos_matrix, predictions, off0, off1)
    
    # 2. STORE NEW PREDICTION
    for code in codes:
        predictions.append([txt[off0:off1], off0, off1, original_label, code])   
        pos_matrix.append([off0, off1])
        
    return predictions, pos_matrix


def eliminate_contained_annots(pos_matrix, new_annotations, off0, off1):
    '''
    DESCRIPTION: function to be used when a new annotation is found. 
              It check whether this new annotation contains in it an already 
              discovered annotation. In that case, the old annotation is 
              redundant, since the new one contains it. Then, the function
              removes the old annotation.
    '''
    to_eliminate = [pos for item, pos in zip(pos_matrix, range(0, len(new_annotations))) 
                    if (off0<=item[0]) & (item[1]<=off1)]
    new_annotations = [item for item, pos in zip(new_annotations, range(0, len(new_annotations)))
                       if pos not in to_eliminate]
    pos_matrix = [item for item in pos_matrix if not (off0<=item[0]) & (item[1]<=off1)]
    
    return pos_matrix, new_annotations


def check_surroundings(txt, span, original_annot, n_chars, n_words, original_label,
                       predictions, pos_matrix, min_upper, code):
    '''
    DESCRIPTION: explore the surroundings of the match.
              Do not care about extra whitespaces or punctuation signs in 
              the middle of the annotation.
    '''
    
    ## 1. Get normalized surroundings ##
    large_span = txt[max(0, span[0]-n_chars):min(span[1]+n_chars, len(txt))]

    # remove half-catched words
    try:
        first_space = re.search('( |\n)', large_span).span()[1]
    except: 
        first_space = 0
    try:
        last_space = (len(large_span) - re.search('( |\n)', large_span[::-1]).span()[0])
    except:
        last_space = len(large_span)
    large_span_reg = large_span[first_space:last_space]
    
    # Tokenize text span 
    token_span2id, id2token_span_pos, token_spans = tokenize_span(large_span_reg,
                                                                  n_words)
    # Normalize
    original_annotation_processed = normalize_str(original_annot, min_upper)
    token_span_processed2token_span = normalize_tokens(token_spans, min_upper)
    
    ## 2. Match ##
    try:
        res = token_span_processed2token_span[original_annotation_processed]
        id_ = token_span2id[res]
        pos = id2token_span_pos[id_]
        off0 = (pos[0] + first_space + max(0, span[0]-n_chars))
        off1 = (pos[1] + first_space + max(0, span[0]-n_chars))
        
        # Check new annotation is not contained in a previously stored new annotation
        if not any([(item[0]<=off0) & (off1<= item[1]) for item in pos_matrix]):
            # STORE PREDICTION and eliminate old predictions contained in the new one.
            predictions, pos_matrix = store_prediction(pos_matrix, predictions,
                                                       off0, off1, original_label,
                                                       original_annot, txt, code)
    except: 
        pass
    
    return predictions, pos_matrix