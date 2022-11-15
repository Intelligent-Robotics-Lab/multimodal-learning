import json

with open('../data/wikihow-instructions.json') as f:
    wikihow_data = json.load(f).values()
with open('../data/actions.txt', 'w+') as f:
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
