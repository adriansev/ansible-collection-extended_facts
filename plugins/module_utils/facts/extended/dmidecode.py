# Collect facts related to dmidecode
#
# This file is part of Ansible Extended Facts
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import copy
from itertools import groupby

from ansible.module_utils.facts.collector import BaseFactCollector
from ansible.module_utils.facts.utils import get_file_content, get_file_lines

class DmidecodeFactCollector(BaseFactCollector):
    name = 'dmidecode'
    _fact_ids = set()

    def collect(self, module = None, collected_facts = None):
        facts_dict = {}

        jc_present = True
        try:
            import jc
        except Exception:
            print('jc is not installed!!! do: python3 -m pip install --upgrade jc')
            jc_present = False

        dmidecode_bin = module.get_bin_path('dmidecode')
        if not dmidecode_bin or not jc_present: return facts_dict
        rc, dmidecode_out, err = module.run_command([dmidecode_bin])

        dmi_list = jc.parse('dmidecode', dmidecode_out) if dmidecode_out else None
        if not dmi_list: return facts_dict
        dmi_ini = copy.deepcopy(dmi_list)

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

        def convert_dmi_field(f_dmi_in: dict):
            if not f_dmi_in or not isinstance(f_dmi_in, dict): return None
            f_dmi_in.pop('handle', None)
            if 'values' not in f_dmi_in or not f_dmi_in['values']: return None
            f_dmi_in['values'].pop('type', None)  # if there is a type (string) in values, skip it
            return { 'type': f_dmi_in['type'], **f_dmi_in['values'] }

        def key_type(field): return field['type']

        dmi_out = [ convert_dmi_field(f) for f in dmi_list ]
        [ dmi_out.remove(x) for x in dmi_out if not x ]
        dmi_out = sorted(dmi_out, key = key_type)

        dmi_out_types = {}
        for entry_type, entry_values in groupby(dmi_out, key = key_type):
            dmi_out_types[type2str[entry_type]] = list(entry_values)
            [ f.pop('type') for f in dmi_out_types[type2str[entry_type]] ]

        if dmi_out_types:
            facts_dict['dmidecode'] = dmi_out_types

        return facts_dict

