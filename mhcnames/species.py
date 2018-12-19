# Copyright (c) 2018. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function, division, absolute_import

from collections import OrderedDict

from .parsed_result import ParsedResult
from .data import gene_ontology as raw_gene_ontology_dict
from .data import gene_aliases as raw_gene_aliases_dict
from .data import serotypes as raw_serotypes_dict
from .data import haplotypes as raw_haplotypes_dict
from .data import allele_aliases as raw_allele_aliases_dict

from .species_data import prefix_to_common_names


class Species(ParsedResult):
    """
    Representation of a parsed species prefix such as "HLA", "ELA"
    """
    def __init__(self, species_prefix):
        self.species_prefix = species_prefix
        self._genes = None
        self._gene_set = None
        self._expanded_gene_alias_dict = None

    @property
    def prefix(self):
        return self.species_prefix

    def __str__(self):
        return "Species(species_prefix='%s')" % (self.species_prefix,)

    def field_names(self):
        return ("species_prefix",)

    def to_record(self):
        return OrderedDict([
            ("species_prefix", self.species_prefix),
            ("species_name", self.common_species_name),
        ])

    @property
    def common_species_name(self):
        """
        Returns common species name associated with MHC species
        prefix.

        TODO: get this look-up table from a YAML file, instead of hard-coding
        """
        return prefix_to_common_names.get(self.species_prefix)

    @property
    def gene_ontology(self):
        """
        Dictionary containing keys which are a subset of
        {I, Ia, Ib, Ic, Id, II, IIa, IIb}.
        The class I entries map to lists of genes and the class II entries map
        to dictionaries such as:
            {"DR": ["DRA", "DRB1", "DRB3", "DRB5"]}
        """
        return raw_gene_ontology_dict.get(self.species_prefix, {})

    @property
    def gene_aliases(self):
        """
        Dictionary mapping non-canonical gene names to their canonical forms.
        """
        return raw_gene_aliases_dict.get(self.species_prefix, {})

    @property
    def allele_aliases(self):
        """
        Dictionary mapping non-canonical allele names to their canonical forms.
        """
        return raw_allele_aliases_dict.get(self.species_prefix, {})

    @property
    def serotypes(self):
        """
        Dictionary mapping serotype names to lists of alleles
        (all expected to be for the same gene)
        """
        return raw_serotypes_dict.get(self.species_prefix, {})

    @property
    def haplotypes(self):
        """
        Dictionary mapping haplotype names to lists of alleles (one per gene)
        """
        return raw_haplotypes_dict(self.species_prefix, {})

    def genes(self):
        if self._genes is None:
            self._genes = self._collect_genes()
        return self._genes

    def gene_set(self):
        if self._gene_set is None:
            self._gene_set = set(self.genes())
        return self._gene_set

    def expanded_gene_aliases(self):
        if self._expanded_gene_alias_dict is None:
            self._expanded_gene_alias_dict = self._create_expanded_gene_aliases()
        return self._expanded_gene_alias_dict

    def _collect_genes(self):
        """
        Create a dictionary mapping each species to a set of genes
        """
        all_genes = []
        for class1_category in {"I", "Ia", "Ib", "Ic", "Id"}:
            class1_genes = self.gene_ontology.get(class1_category, [])
            all_genes.extend(class1_genes)
        for class2_category in {"II", "IIa", "IIb"}:
            class2_genes_dict = self.gene_ontology.get(class2_category, {})
            for class2_genes in class2_genes_dict.values():
                all_genes.extend(class2_genes)
        return all_genes

    def find_matching_gene_name(self, gene_name):
        """
        Use known aliases and normalized capitlization to infer
        the canonical gene name corresponding to the input.
        """
        if gene_name in self.gene_set():
            return gene_name
        return self.expanded_gene_aliases().get(gene_name.upper())

    def normalize_gene_name_if_exists(self, gene_name):
        normalized_name = self.find_matching_gene_name(gene_name)
        if normalized_name:
            return normalized_name
        else:
            return gene_name

    def _create_expanded_gene_aliases(self):
        expanded_aliases = {}
        for gene in self.genes():
            expanded_aliases[gene] = gene
            upper = gene.upper()
            if upper != gene:
                expanded_aliases[upper] = gene

        for original_alias, gene_name in self.gene_aliases.items():
            expanded_alias_set = {
                original_alias,
                original_alias.replace("-", ""),
                original_alias.upper(),
                original_alias.replace("-", "").upper()
            }
            for alias in expanded_alias_set:
                expanded_aliases[alias] = gene_name

        return expanded_aliases

    def get_mhc_class_of_gene(self, gene_name):
        """
        Parameters
        ----------
        gene_name : str

        Returns either one of "I", "Ia", "Ib", "Ic", "Id", "II", IIa", "IIb"
        or None if species can't be found
        """
        gene_name = self.find_matching_gene_name(gene_name)
        for mhc_class, mhc_class_members in self.gene_ontology.items():
            if mhc_class in {"I", "Ia", "Ib", "Ic", "Id"}:
                for member_gene in mhc_class_members:
                    if member_gene == gene_name:
                        return mhc_class
            elif mhc_class in {"II", "IIa", "IIb"}:
                for locus, genes in mhc_class_members.items():
                    if locus == gene_name:
                        return mhc_class
                    for candidate_gene_name in genes:
                        if candidate_gene_name == gene_name:
                            return mhc_class
        return None


# Many old-fasioned naming systems like "equine" ELA now correspond
# to multiple species. For each species-ambiguous prefix, map it to the
# species which has the most complete gene annotations.
exemplar_species = {
    "DLA": "Calu",
    "ELA": "Eqca",
    "OLA": "Ovar",
    "SLA": "Susc",
    "RT1": "Rano"
}

special_prefixes = set(exemplar_species.keys())

# map prefixes to Species objects
species_dict = {}
for species_prefix, species_gene_ontology in raw_gene_ontology_dict.items():
    species_dict[species_prefix] = Species(species_prefix)


def create_species_aliases():
    """
    Create dictionary of species aliases from both the species->MHC class->gene
    ontology and the set of MHC names (like RT1) which actually represent
    multiple species and require an exemplar to be chosen for its gene
    metadata.
    """
    aliases = species_dict.copy()
    for group_name, species_name in exemplar_species.items():
        aliases[group_name] = species_dict[species_name]

    for key, species in list(species_dict.items()):
        upper = key.upper()
        if upper != key:
            aliases[upper] = species
        upper_no_dash = upper.replace("-", "")
        if upper_no_dash not in {key, upper}:
            aliases[upper_no_dash] = species
    return aliases

# dictionary mapping alias names to Species objects
species_aliases_dict = create_species_aliases()


def find_matching_species(name):
    """
    Returns either SpeciesInfo object or None if species can't be found
    """
    if name in species_dict:
        return species_dict[name]
    return species_aliases_dict.get(name.upper().replace("-", ""))


def find_matching_species_prefix(name):
    """
    Returns normalized prefix for given species but will keep
    RT1, DLA, ELA, OLA, SLA from normalizing to a particular member
    of their species group.
    """
    upper_no_dash = name.upper().replace("-", "")
    if upper_no_dash in exemplar_species:
        return upper_no_dash
    species = find_matching_species(name)

    if species is not None:
        return species.species_prefix
    else:
        return None


def infer_species_prefix_substring(name):
    """
    Trying to parse prefixes of alleles such as:
        HLA-A
    but also ones with dashes in the species prefix:
        H-2-K
    and also those lacking any dashes such as:
        H2K

     ...we also need to consider that alleles, haplotypes, etc may come
     immediately after the gene:
        H2Kk
        HLA-A0201

    Returns the normalized species prefix and the original string that matched
    it or None.
    """
    # Try parsing a few different substrings to get the species,
    # and then use the species gene list to determine what the gene is in this string
    candidate_species_substrings = [name]

    if "-" in name:
        # if name is "H-2-K" then try parsing "H" and "H-2" as a species
        # prefix
        parts_split_by_dash = name.split("-")
        candidate_species_substrings.extend([
            parts_split_by_dash[0],
            parts_split_by_dash[0] + "-" + parts_split_by_dash[1]
        ])
    for seq in candidate_species_substrings:
        for n in [2, 3, 4]:
            original_prefix = seq[:n]
            normalized_prefix = find_matching_species_prefix(name[:n])
            if normalized_prefix is not None:
                return normalized_prefix, original_prefix
    return None