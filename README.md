# Detect new annotations in Text files based on TSV with codes and spans.

## Getting Started

Scripts written in Python 3.7, anaconda distribution Anaconda3-2019.07-Linux-x86_64.sh

### Prerequisites

(You need to have installed python3 and its base libraries, plus:
+ spacy
+ pandas
+ numpy

### Installing

```
git clone <repo_url>
```

## Running the scripts

```
cd mesinesp-baseline/src
python new_detection_method.py -d /path/to/input/json_file.json -i /path/to/input/TSV_file.tsv -o /path/to/output/folder/
```
This creates output_file.txt in /path/to/output/folder/ with the detected suggestions.

## Procedure Description

##### Steps:
1. Parse annotation information in TSV.
2. Find text spans in -d that are in TSV. Assign a DeCS code to them.
3. Write JSON file in -o

##### Arguments:
+ **Input**: 
	+ -d option: text files.
	+ -i option: annotation information: TSV with 2 columns: code, span.

+ **Output**: 
	+ -o option. Output folder where output file will be created.



##### To execute it: 
```
cd mesinesp-baseline/src
python new_detection_method.py -i ../data/decs_terms_and_synonyms_uniq.tsv -d ../data/Task_MESINESP-Batch1-Week1_raw.json -o ../../
```
This creates output_file.json in ../../.


## Built With

* [Python3.7](https://www.anaconda.com/distribution/)

## Authors

* **Antonio Miranda** - antonio.miranda@bsc.es


