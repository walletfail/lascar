"""
This file is part of lascar

lascar is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr

"""

"""
multiple_container.py

    MultipleContainer concatenate containers already instanciated.

"""
import numpy as np

from .container import AbstractArray, Container, TraceBatchContainer


class MultipleContainer(Container):

    def __init__(self, *args, **kwargs):
        """
        Constructor.
        :param args: a *list of containers to be concatenated into the MultipleContainer
        """
        self._containers = args
        self.number_of_traces = sum([len(container) for container in args])
        self.leakages = AbstractArray((self.number_of_traces,) + self._containers[0].leakages.shape[1:],
                                      self._containers[0].leakages.dtype)
        self.values = AbstractArray((self.number_of_traces,) + self._containers[0].values.shape[1:],
                                    self._containers[0].values.dtype)

        Container.__init__(self, **kwargs)
        self.logger.debug('Creating MultipleContainer using %d Container.' % len(self._containers))

        # improvement (todo)
        current = 0
        self._t = np.zeros((self.number_of_traces + 1, 2), int)
        for i, container in enumerate(args):
            self._t[current:current + container.number_of_traces, 0] = i
            self._t[current:current + container.number_of_traces, 1] = range(container.number_of_traces)
            current += container.number_of_traces
        self._t[current] = i, container.number_of_traces

    def __getitem__(self, item):
        self.logger.debug("__getitem__ with key %s %s" % (str(item), type(item)))

        if isinstance(item, int):
            container_idx, suboffset = self._t[item]
            return self._containers[container_idx][suboffset]

        elif isinstance(item, slice):
            # check contiguity:
            if item.step is not None and item.step > 1:
                raise ValueError("MultipleContainer __getitem__ slice elements must be contiguous")
            offset_begin = item.start if item.start else 0
            offset_end = item.stop if item.stop else self.number_of_traces

        elif isinstance(item, list):
            # check contiguity:
            if np.any(np.diff(np.array(item)) != 1):
                raise ValueError("MultipleContainer __getitem__ list elements must be contiguous")
            offset_begin = item[0]
            offset_end = item[-1]
        else:
            raise ValueError("MultipleContainer __getitem__ only accepts int, list and slices (contiguous)")

        container_offset_begin, suboffset_offset_begin = self._t[offset_begin]
        container_offset_end, suboffset_offset_end = self._t[offset_end]

        # if container_offset_begin == container_offset_end:
        #     return self._containers[container_offset_end][suboffset_offset_begin:suboffset_offset_end]
        #
        # else:
        #     leakages = np.empty((offset_end - offset_begin,) + self._leakage_abstract.shape, self._leakage_abstract.dtype)
        #     values = np.empty((offset_end - offset_begin,) + self._value_abstract.shape, self._value_abstract.dtype)
        #     #first container:
        #     leakages[:len(container_offset_begin)-suboffset_offset_begin] =

        suboffsets = []
        if container_offset_begin == container_offset_end:
            suboffsets.append([container_offset_begin, suboffset_offset_begin, suboffset_offset_end])
        else:
            suboffsets.append([container_offset_begin, suboffset_offset_begin,
                               self._containers[container_offset_begin].number_of_traces])
            for i in range(container_offset_begin + 1, container_offset_end):
                suboffsets.append([i, 0, self._containers[i].number_of_traces])
            suboffsets.append([container_offset_end, 0, suboffset_offset_end])

        leakages = np.empty((offset_end - offset_begin,) + self._leakage_abstract.shape, self._leakage_abstract.dtype)
        values = np.empty((offset_end - offset_begin,) + self._value_abstract.shape, self._value_abstract.dtype)

        i = 0
        for suboffset in suboffsets:
            batch = self._containers[suboffset[0]][suboffset[1]:suboffset[2]]
            leakages[i:i + len(batch)] = batch.leakages
            values[i:i + len(batch)] = batch.values
            i += len(batch)
        return TraceBatchContainer(leakages, values)

    @property
    def leakage_section(self):
        return self._leakage_section

    @leakage_section.setter
    def leakage_section(self, section):
        for c in self._containers:
            c.leakage_section = section
        self._leakage_section = section
        self._leakage_section_abstract = c._leakage_section_abstract
        self._leakage_abstract = c._leakage_abstract

    @property
    def leakage_processing(self):
        return self._leakage_processing

    @leakage_processing.setter
    def leakage_processing(self, processing):
        for c in self._containers:
            c.leakage_processing = processing
        self._leakage_processing = processing
        self._leakage_section_abstract = c._leakage_section_abstract
        self._leakage_abstract = c._leakage_abstract

    @property
    def value_section(self):
        return self._value_section

    @value_section.setter
    def value_section(self, section):
        for c in self._containers:
            c.value_section = section
        self._value_section = section
        self._value_section_abstract = c._value_section_abstract
        self._value_abstract = c._value_abstract

    @property
    def value_processing(self):
        return self._value_processing

    @value_processing.setter
    def value_processing(self, processing):
        for c in self._containers:
            c.value_processing = processing
        self._value_processing = processing
        self._value_section_abstract = c._value_section_abstract
        self._value_abstract = c._value_abstract
