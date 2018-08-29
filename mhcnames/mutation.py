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

import re

from serializable import Serializable

from .allele_parse_error import AlleleParseError

class Mutation(Serializable):
    def __init__(self, pos, aa_original, aa_mutant):
        self.pos = pos
        self.aa_original = aa_original
        self.aa_mutant = aa_mutant

    def normalized_string(self):
        return "%s%d%s" % (self.aa_original, self.pos, self.aa_mutant)

    mutation_regex = re.compile("([A-Z])(\d)([A-Z])")

    @classmethod
    def parse(cls, seq):
        seq = seq.upper()
        result = cls.mutation_regex.full_match(seq)
        if result is None:
            raise AlleleParseError("Allele mutation malformed: '%s'")
        aa_original = result.group(1)
        pos = int(result.group(2))
        aa_mutant = result.group(3)
        return Mutation(pos, aa_original, aa_mutant)