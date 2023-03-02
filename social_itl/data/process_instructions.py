import json
from .dataset import get_dataset_path

with open(get_dataset_path('wikihow-instructions.json')) as f:
    wikihow_data = json.load(f).values()
with open(get_dataset_path('actions.txt'), 'w+') as f:
    for instruction in wikihow_data:
        instruction = instruction.lower()
        if ' if ' in instruction:
            print(instruction)
            continue
        elif ' say ' in instruction:
            print(instruction)
            continue
        else:
            f.write(instruction + '\n')
