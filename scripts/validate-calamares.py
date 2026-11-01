#!/usr/bin/env python3
"""Check our Calamares modules against the matching upstream source schemata."""
from pathlib import Path
import argparse
import jsonschema
import yaml

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('upstream', type=Path)
parser.add_argument('--profile', type=Path, default=Path(__file__).resolve().parents[1] / 'profile')
args = parser.parse_args()
for config in (args.profile / 'airootfs/etc/calamares/modules').glob('*.conf'):
    schema_path = args.upstream / f'src/modules/{config.stem}/{config.stem}.schema.yaml'
    schema = yaml.safe_load(schema_path.read_text())
    if config.stem == 'partition':
        # 3.4.3 documents and implements these fields but omits them from its schema.
        implementation = (args.upstream / 'src/modules/partition/PartitionViewStep.cpp').read_text()
        for key, rule in {
            'defaultPartitionTableType': {'type': 'string', 'enum': ['gpt', 'msdos']},
            'createHybridBootloaderLayout': {'type': 'boolean'},
        }.items():
            assert f'"{key}"' in implementation, f'Upstream no longer implements {key}'
            schema['properties'][key] = rule
    jsonschema.validate(yaml.safe_load(config.read_text()), schema)
    print('Validated:', config.name)
