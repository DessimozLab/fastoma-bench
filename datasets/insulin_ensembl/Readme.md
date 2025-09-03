# Insulin GeneTree From Ensembl Datatset

this dataset contains the Ensembl GeneTree for the Insulin gene family (ENSG00000254647). It serves as an example dataset.

The dataset includes both the raw input files from Ensembl and the converted version 
suitable to run with FastOMA. The conversion is done with the `convert.py` script.

## Raw Input files
- INS_gene_tree.xml: XML file with the gene tree from Ensembl.
- Ensembl_gene_tree.nwk: Newick formatted gene tree from Ensembl.

## Input files
- HOG_00001.fa: Fasta file with the protein sequences of the insulin gene family, according to Ensembl.
- species_tree.nwk: Newick formatted species tree for the species included in the insulin gene family.
- asserted.yml: YAML file with the asserted orthologs according to Ensembl.

HOG_00001.fa and species_tree.nwk files can be generated with the `convert.py` script.

The asserted.yml file is manually curated and asserts a duplication event in the lineage leading to the mices.







