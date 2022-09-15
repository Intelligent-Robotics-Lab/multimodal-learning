import json
import re
import datasets
from itertools import cycle
from typing import Dict, List

def fill_template(template: str, wildcards: List[str], grammar: Dict) -> List[str]:
    if len(wildcards) == 0:
        return [template]
    w = wildcards[-1]
    if w == 'phrase' or w == 'that-phrase':
        return fill_template(template, wildcards[:-1], grammar)
    elif w == 'question':
        return fill_template(template, wildcards[:-1], grammar)
    elif w == 'imp':
        return fill_template(template, wildcards[:-1], grammar)
    elif 'pronoun' in w:
        return fill_template(template, wildcards[:-1], grammar)
    else:
        return [t for p in enumerate_pattern(w, grammar) for t in fill_template(template.replace(f'{{{w}}}', p), wildcards[:-1], grammar)]

def fill_pronouns(template: str):
    if 'pronoun' not in template:
        return [template]
    output = []
    # wildcards = re.findall('\{(pronoun.*?)\}', template)

    singular = False
    plural = False
    if 'pronoun-subj-s' in template:
        singular = True
    elif 'pronoun-subj-pl' in template:
        plural = True

    if singular:
        for gender in ['m', 'f']:
            t = template
            # for w in wildcards:
            if gender == 'm':
                t = t.replace('{pronoun-subj-s}', 'he')
                t = t.replace('{pronoun-obj}', 'him')
                output.append(t)
            else:
                t = t.replace('{pronoun-subj-s}', 'she')
                t = t.replace('{pronoun-obj}', 'her')
                output.append(t)
            
    elif plural:
        t = template
        t = t.replace('{pronoun-subj-pl}', 'they')
        t = t.replace('{pronoun-obj}', 'them')
        output.append(t)

    else:
        t = template.replace('{pronoun-obj}', 'him')
        output.append(t)
        t = template.replace('{pronoun-obj}', 'her')
        output.append(t)
        t = template.replace('{pronoun-obj}', 'them')
        output.append(t)
    return output

def enumerate_pattern(pattern: str, grammar: Dict):
    try:
        enumerate_pattern.cache
    except AttributeError:
        enumerate_pattern.cache = {}
    if pattern in enumerate_pattern.cache:
        return enumerate_pattern.cache[pattern]
    else:
        expanded = []
        # print(pattern)
        for template in grammar[pattern]:
            wildcards = re.findall('\{(.*?)\}', template)
            expanded += fill_template(template, wildcards, grammar)
        enumerate_pattern.cache[pattern] = expanded
        return expanded
    

def build_tree(file: str):
    templates = []
    with open(file, 'r') as f:
        grammar: Dict = json.load(f)
        root_elements: Dict = grammar['root']
        nonroot_elements: Dict = grammar['nonroot']
        all_elements = {**root_elements, **nonroot_elements}
        # # use dynamic programming to save time
        # cached_patterns = {}
        for pattern in root_elements.keys():
            # print(pattern)
            pattern = enumerate_pattern(pattern, all_elements)
            templates += [t for p in pattern for t in fill_pronouns(p)]
    return templates

def load_questions():
    dataset = datasets.load_from_disk('../data/daily_dialog_questions')
    # print(len(dataset))
    dataset = dataset.filter(lambda x: x['sentence'].count(' ') > 0 and x['sentence'].count('"') == 0)
    # print(len(dataset))
    return dataset

def load_statements():
    dataset = datasets.load_from_disk('../data/daily_dialog_statements')
    # print(len(dataset))
    dataset = dataset.filter(lambda x: x['sentence'].count(';') == 0 and x['sentence'].count('"') == 0)
    # print(len(dataset))
    return dataset

def load_imperatives():
    dataset = datasets.load_dataset("text", data_files="../data/imperatives.txt")["train"]
    def preprocess(x):
        x['text'] = x['text'].lower()
        x['text'] = x['text'].split('.')[0]
        x['text'] = x['text'].replace('!', '')
        x['text'] = x['text'].replace(',', '')
        return x
    dataset = dataset.map(preprocess)
    def filter_imperatives(x):
        return not (x['text'].startswith(('dont', 'don\'t', 'do ', 'let\'s', 'let us', 'if ', 'this ')) or ';' in x['text'] or '"' in x['text'])
    dataset = dataset.filter(filter_imperatives)
    return dataset

if __name__ == '__main__':
    templates = build_tree('templates.json')
    
    questions = cycle(load_questions().shuffle()["sentence"])
    statements = cycle(load_statements().shuffle()["sentence"])
    imperatives = cycle(load_imperatives().shuffle()["text"])
    filled_statements = []
    for template in templates:
        if 'that-phrase' in template:
            continue
        for i in range(40):
            t = template
            while '{phrase}' in t:
                t = t.replace('{phrase}', f'"{next(statements)}"', 1)
            while '{question}' in t:
                t = t.replace('{question}', f'"{next(questions)}"', 1)
            while '{imp}' in t:
                t = t.replace('{imp}', f'"{next(imperatives)}"', 1)
            filled_statements.append(t)
            print(t)
    dataset = datasets.Dataset.from_dict({'sentence': filled_statements})
    dataset.save_to_disk('../data/filled-templates')