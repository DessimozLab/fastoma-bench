# Fastoma-Bench

This repo contains benchmarks for [FastOMA](https://github.com/DessimozLab/FastOMA), that are run on a regular basis.

View the latest results here: https://dessimozlab.github.io/fastoma-bench/

## Overview of the repository

The repository is structured as follows:

```
├── benchmarks
│   └── history
│       ├── ds01.json
│       ├──  ...
│       └── dsXX.json
├── datasets
│   ├── ds01
│   ├── ...
│   ├── insulin_ensembl
│   │   ├── asserted.yml
│   │   ├── convert.py
│   │   ├── Ensembl_Species_tree.newick
│   │   ├── HOG_00001.fa
│   │   ├── INS_gene_tree.xml
│   │   ├── Readme.md
│   │   └── species_tree.nwk
│   └── manifest.json
├── docs
│   └── index.html
├── pyproject.toml
├── README.md
├── scripts
│   ├── make_dashboard.py
│   ├── parse_metrics.py
│   ├── run_bench_batch_docker.py
│   └── util.py
```

The most important folder is the `datasets` folder, which contains the datasets used for the benchmarks. 
Each dataset is in its own folder, named in whatever way the user wants.

As of now, the datasets can benchmark either the *OMAmer* aspect of FastOMA, or the *subhog inference* step.
For the subhog inference step, the dataset `insulin_ensembl` serves as an example. It contains the sequences
passed to the subhog inference step `HOG_00001.fa`, the input species tree with matching labels, and the file 
`asserted.yml` which contains assertions of the expected output.

## Running the benchmarks
The benchmarks can be run locally by calling the script `scripts/run_bench_batch_docker.py`. Note that this 
repository must be installed in a virtual environment beforehand and that docker must be installed.

The script will run all benchmarks defined in the datasets/manifest.json file, and for each dataset, the 
metrics will be computed and stored in a per-dataset folder json file in `benchmarks/history/dsXX.json`.

The script `scripts/make_dashboard.py` can be used to generate a dashboard from the json files in `benchmarks/history/`

Note that the whole process is also being automated in the CI pipeline, and should run automatically on every push 
commit of this repository and on a daily basis, and the results are being pushed to following github page: 
https://dessimozlab.github.io/fastoma-bench/


## Contributing benchmarks

If you want to contribute a benchmark, feel free to add a new folder to the `datasets/` folder and add the 
dataset to the `datasets/manifest.json` file.

### datasets/manifest.json
The `datasets/manifest.json` file contains a list of all datasets that are being benchmarked. Each dataset is 
described by a dictionary with the following keys:

- id: An ID for the dataset. in the format "ds01"
- step: step of the FastOMA pipeline to be benchmarked. supported are "subhog_inference" and "omamer".
- tier: one of "tiny", "medium" and "full". 'medium' and 'full' are only occationally run in the CI. 
- input_path: path to the directory of the dataset, e.g. "datasets/insulin_ensembl". 
- subhog_inference specific keys:
  - sp_tree the name of the species tree file inside the input_path, e.g. "species_tree.nwk".
  - args: a dictionary with additional arguments to be passed to he fastoma-sunhog-inference step.
- omamer specific keys:
  - tbd
  

### Notes about SubHOG inference benchmarks
The family file needs to be called `HOG_xxxxxx.fa`, where `xxxxxx` is a numeric identifier. Also, the fasta header needs 
to be in a specific format:
```
>prot_id||species_id||numeric_gene_id
SEQUENCE
```
where the `prot_id` is a unique identifier for the protein, `species_id` is the identifier of the species 
(it must match the species tree labels), and `numeric_gene_id` is a numeric identifier for the gene 
(it can be any number, but it must be numeric. This will be the orthoxml geneRef id).

The `species_tree.nwk` file needs to be in newick format, and the `species_tree.nwk` file needs to be in newick format, 
in a way that ete3 can parse it (no quotes, no spaces, no brackets, etc). The species names in the tree must match 
the `species_id` in the fasta header.

The `insulin_ensembl` dataset is an example. it contains also a convert.py script, which was used to convert the 
ensembl compara species tree and phyloxml genetrees into the required format.

#### Asserted.yml file
The asserted.yml file contains the assertions of the expected output. The format is still likely to be changed in the 
future, but the example in the `insulin_ensembl` folder should give a good idea and is rather simple to understand. 


### Notes about OMAmer benchmarks
The OMAmer benchmarks are currently not yet implemented.