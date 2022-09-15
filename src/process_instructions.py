import json
import spacy

nlp = spacy.load("en_core_web_sm")
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
        
        doc = nlp("You should " + instruction)
        if doc[2].pos_ != 'VERB':
            print(doc)
        # print(instruction)
        # print(nlp(instruction)[2].pos_)
