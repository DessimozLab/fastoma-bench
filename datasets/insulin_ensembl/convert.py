import collections

import Bio.Phylo
import Bio.SeqIO
import itertools
import ete3

# convert species tree
with open('Ensembl_Species_tree.newick','rt') as fh:
    nwk = fh.read().replace(' ','_')
sp = ete3.Tree(nwk, format=1)
name2node = collections.defaultdict(list)
for n in sp.traverse():
    name2node[n.name].append(n)
cnt = 0
for name, nodes in name2node.items():
    if len(nodes) > 1:
        for node in nodes:
            cnt += 1
            node.name = f"{name}_{cnt:03d}"
sp.write(outfile='species_tree.nwk', format=1)

t = list(Bio.Phylo.parse('INS_gene_tree.xml', 'phyloxml'))[0]

seqs = []
for l in t.get_terminals():
    r = l.sequences[0].to_seqrecord()
    r.species = l.taxonomy.scientific_name.replace(' ','_').replace('(','').replace(')','')
    r.id = l.name
    seqs.append(r)
seqs.sort(key=lambda r:r.species)
with open('insulin.fa', 'wt') as fh:
    for c, (grp, genes) in enumerate(itertools.groupby(seqs, key=lambda r:r.species), start=1001):
        for k, g in enumerate(genes, start=1):
            g.id = (g.id.split(':')[-1] + f"||{g.species}||{c}{k:05d}")
            g.description = ""
            Bio.SeqIO.write(g, fh, format='fasta')
