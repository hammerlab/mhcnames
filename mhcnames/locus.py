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

from serializable import Serializable

from .species import get_mhc_class

class Locus(Serializable):
    def __init__(self, species_prefix, gene_name):
        self.species_prefix = species_prefix
        self.gene_name = gene_name

    def get_mhc_class(self):
        return get_mhc_class(self.species_prefix, self.gene_name)

    def normalized_string(self, include_species=True):
        if include_species:
            return "%s-%s" % (self.species_prefix, self.gene_name)
        else:
            return self.gene_name

    def compact_string(self, include_species=True):
        """
        Compact representation of a Locus, currently same as the
        normalized representation.
        """
        return self.normalized_string(include_species=include_species)

    def to_locus(self):
        """
        Descendant classes use this method to project their fields down
        to a Locus object.
        """
        if self.__class__ is Locus:
            return self
        else:
            return Locus(self.species_prefix, self.gene_name)

    def is_mutant(self):
        return False

    def to_dict(self):
        """
        Returns dictionary with all fields of this locus, its normalized,
        representation and the values of the following methods:
            - is_mutant
            - get_mhc_class
        """
        return OrderedDict([
            ("locus", self.normalized_string()),
            ("species_prefix", self.species_prefix),
            ("gene_name", self.gene_name),
            ("is_mutant", self.is_mutant()),
            ("mhc_class", self.get_mhc_class()),
        ])