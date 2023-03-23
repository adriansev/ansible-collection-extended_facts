# Collect facts related to dmidecode
#
# This file is part of Ansible Extended Facts
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import json
from itertools import groupby
from itertools import chain

from ansible.module_utils.facts.collector import BaseFactCollector

class DmidecodeFactCollector(BaseFactCollector):
    name = 'dmidecode'
    _fact_ids = set()

    def collect(self, module = None, collected_facts = None):
        facts_dict = {}
        extd_facts_log = '/tmp/extended_facts.log'
        with open(extd_facts_log, 'w') as f: f.write('Start of extended facts gathering log\n')

        try:
            import jc
        except Exception:
            with open(extd_facts_log, 'a') as f: f.write('jc is not installed!!! do: python3 -m pip install --upgrade jc\n')
            return facts_dict

        dmidecode_bin = module.get_bin_path('dmidecode')
        if not dmidecode_bin:
            with open(extd_facts_log, 'a') as f: f.write('No dmidecode command found\n')
            return facts_dict

        rc, dmidecode_out, err = module.run_command([dmidecode_bin])
        if not dmidecode_out:
            with open(extd_facts_log, 'a') as f: f.write(f'No dmidecode output!Exitcode:{rc}\n{err}\n')
            return facts_dict

        dmi_list = jc.parse('dmidecode', dmidecode_out) if dmidecode_out else None
        if not dmi_list:
            with open(extd_facts_log, 'a') as f: f.write('No output from jc parsing of dmidecode_out\n')
            return facts_dict

        # with open(extd_facts_log, 'a') as f: f.write(f'\n\ndmi_list:\n{dmi_list}\n\n')

        # http://git.savannah.nongnu.org/cgit/dmidecode.git/tree/dmidecode.c#n162
        type2str = { 0: 'BIOS', 1: 'System', 2: 'Baseboard', 3: 'Chassis', 4: 'Processor', 5: 'Memory Controller',
                     6: 'Memory Module', 7: 'Cache', 8: 'Port Connector', 9: 'System Slots', 10: 'On Board Devices',
                    11: 'OEM Strings', 12: 'System Configuration Options', 13: 'BIOS Language', 14: 'Group Associations',
                    15: 'System Event Log', 16: 'Physical Memory Array', 17: 'Memory Device', 18: '32-bit Memory Error',
                    19: 'Memory Array Mapped Address', 20: 'Memory Device Mapped Address', 21: 'Built-in Pointing Device',
                    22: 'Portable Battery', 23: 'System Reset', 24: 'Hardware Security', 25: 'System Power Controls', 26: 'Voltage Probe',
                    27: 'Cooling Device', 28: 'Temperature Probe', 29: 'Electrical Current Probe', 30: 'Out-of-band Remote Access',
                    31: 'Boot Integrity Services', 32: 'System Boot', 33: '64-bit Memory Error', 34: 'Management Device', 35: 'Management Device Component',
                    36: 'Management Device Threshold Data', 37: 'Memory Channel', 38: 'IPMI Device', 39: 'Power Supply', 40: 'Additional Information',
                    41: 'Onboard Devices Extended Information', 42: 'Management Controller Host Interface', 43: 'TPM Device',
                    44: 'Processor Additional Information', 45: 'Firmware', 46: 'String Property' }

        [ type2str.update({i: f'OEM-specific Type {i}'}) for i in chain(range(47,127), range(128, 255)) ]

        def convert_dmi_field(f_dmi_in: dict):
            if not f_dmi_in or not isinstance(f_dmi_in, dict): return None
            f_dmi_in.pop('handle', None)
            if 'values' not in f_dmi_in or not f_dmi_in['values']: return None
            f_dmi_in['values'].pop('type', None)  # if there is a type (string) in values, skip it
            return { 'type': f_dmi_in['type'], **f_dmi_in['values'] }

        def key_type(field):
            if not field or not isinstance(field, dict): return ''
            if 'type' not in field: return ''
            return field['type']

        dmi_out = [ convert_dmi_field(f) for f in dmi_list ]
        # with open(extd_facts_log, 'a') as f: f.write(f'\n\ndmi_out1({type(dmi_out)}):\n{dmi_out}\n\n')

        dmi_out_clean = list(filter(None, dmi_out))
        dmi_out_sorted = sorted(dmi_out_clean, key = key_type)
        # with open(extd_facts_log, 'a') as f: f.write(f'\n\ndmi_out_sorted:\n{dmi_out_sorted}\n\n')

        dmi_out_types = {}
        with open(extd_facts_log, 'a') as f: f.write('\n\nSTART TYPES\n')
        for entry_type, entry_values in groupby(dmi_out_sorted, key = key_type):
            type_str = type2str[entry_type]
            content = list(entry_values)
            for i in content: i.pop('type')
            if len(content) == 1:
                dmi_out_types[type_str] = content[0]
            else:
                dmi_out_types[type_str] = content

        # with open(extd_facts_log, 'a') as f:
        #     f.write('\n\ndmi_out_types:\n')
        #     f.write(f'{json.dumps(dmi_out_types, indent = 4)}\n\n')

        facts_dict['dmidecode'] = dmi_out_types
        return facts_dict

