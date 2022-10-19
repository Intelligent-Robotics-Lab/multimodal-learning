from __future__ import annotations
from logging import root
from parso import parse
from sklearn.utils import shuffle
import yaml
import datasets
from datasets import Dataset
import re
from itertools import cycle
from typing import Dict, Iterable, List
import random

def preprocess(x):
    x['sentence'] = x['sentence'].lower()
    x['sentence'] = x['sentence'].split('.')[0]
    x['sentence'] = x['sentence'].replace('!', '')
    x['sentence'] = x['sentence'].replace(',', '')
    x['sentence'] = x['sentence'].replace('?', '')
    return x

def load_questions():
    dataset = datasets.load_from_disk('../data/daily_dialog_questions')
    dataset = dataset.filter(lambda x: x['sentence'].count(' ') > 0 and x['sentence'].count('"') == 0)
    dataset = dataset.map(preprocess)
    return dataset

def load_statements():
    dataset = datasets.load_from_disk('../data/daily_dialog_statements')
    dataset = dataset.filter(lambda x: x['sentence'].count(';') == 0 and x['sentence'].count('"') == 0)
    dataset = dataset.map(preprocess)
    return dataset

def load_imperatives():
    dataset = datasets.load_dataset("text", data_files="../data/imperatives.txt")["train"]
    dataset = dataset.rename_column('text', 'sentence')
    dataset = dataset.map(preprocess)
    def filter_imperatives(x):
        return not (x['sentence'].startswith(('dont', 'don\'t', 'do ', 'let\'s', 'let us', 'if ', 'this ')) or ';' in x['sentence'] or '"' in x['sentence'])
    dataset = dataset.filter(filter_imperatives)
    return dataset

def load_actions():
    dataset = datasets.load_dataset("text", data_files="../data/actions.txt")["train"]
    dataset = dataset.rename_column('text', 'sentence')
    dataset = dataset.map(preprocess)
    return dataset

questions = cycle(load_questions().shuffle()["sentence"])
statements = cycle(load_statements().shuffle()["sentence"])
imperatives = cycle(load_imperatives().shuffle()["sentence"])
actions = cycle(load_actions().shuffle()["sentence"])

"""
Algorithm:
Generate a tree of of components, excluding phrases
Lazy iterate through the tree, generating text where needed
"""

dynamic_wildcards = set(['phrase', 'that-phrase', 'question', 'imp', 'action', 'pronoun-subj-s', 'pronoun-subj-pl', 'pronoun-obj'])

class Wildcard:
    def __init__(self, tag: str):
        split_tag = tag.split(':')
        index, name = split_tag if len(split_tag) == 2 else (None, split_tag[0])
        self.name = name
        self.index = index
        self.dynamic = name in dynamic_wildcards

    def __str__(self):
        return f'{{{self.index}:{self.name}}}' if self.index else f'{{{self.name}}}'

class Phrase:
    def __init__(self, template: str, parse: str, grammar: Dict):
        self.template = template
        self.parse = parse
        self.wildcards = [Wildcard(x) for x in re.findall('\{(.*?)\}', template)]
        self.grammar = grammar

    def __str__(self):
        return f'Template({self.template})'
        
    def replace(self, wildcard: Wildcard, replacement: Phrase | str) -> str:
        if isinstance(replacement, Phrase):
            sub_template = replacement.template
            sub_parse = replacement.parse
        else:
            sub_template = replacement
            sub_parse = replacement
        new_template = self.template.replace(f'{str(wildcard)}', sub_template, 1)
        # print(f'Old template: {self.template}')
        # print(f'New template: {new_template}')
        if wildcard.index is None:
            new_parse = self.parse
        else:
            # print("Subbing parse")
            # print(f"Index: {wildcard.index}, replacement: {sub_parse}")
            new_parse = self.parse.replace(wildcard.index, sub_parse, 1)
        # print(f'Old parse: {self.parse}')
        # print(f'New parse: {new_parse}')
        return Phrase(new_template, new_parse, self.grammar)

    def expand(self, recursion_depth=0) -> Iterable[Phrase]:
        # print(f'Expanding {self.template}, recursion depth {recursion_depth}')
        component_wildcards = [x for x in self.wildcards if not x.dynamic]
        base_wildcards = [x for x in self.wildcards if x.dynamic]
        if len(component_wildcards) == 0:
            for w in base_wildcards:
                if w.name == 'imp':
                    yield from (self.replace(w, f'"{i}"') for i in imperatives)
                elif w.name == 'question':
                    yield from (self.replace(w, f'"{q}"') for q in questions)
                elif w.name == 'phrase':
                    yield from (self.replace(w, f'"{s}"') for s in statements)
                elif w.name == 'action':
                    yield from (self.replace(w, f'{a}') for a in actions)
            
            yield from cycle([self])
        else:
            component = self.grammar[component_wildcards[0].name]
            subbed_templates = (self.replace(component_wildcards[0], s) for s in component.enumerate())
            # having enumerated the first wildcard, we can now enumerate the rest
            enumerated_templates = cycle(t.expand(recursion_depth=recursion_depth+1) for t in subbed_templates)
            for t in enumerated_templates:
                yield next(t)

class Component:
    registry = {}
    def __init__(self, name: str, parse: str, sentences: List[str]):
        self.name = name
        self.parse = parse
        self.sentences = shuffle(sentences)
        Component.registry[name] = self

    def __str__(self):
        return f'{self.name} ({self.parse}): {self.sentences}'

    def enumerate(self, num_examples: int = 1) -> Iterable[str]:
        templates = [Phrase(s, self.parse, Component.registry) for s in self.sentences]
        template_expansions = cycle((cycle(t.expand()) for t in templates))
        for t in template_expansions:
            yield next(t)
        # yield from cycle(template_expansions)
# def fill_template(grammar, sentence, num_examples: int) -> List[str]:
def fill_pronouns(phrase: Phrase) -> Phrase:
    template = phrase.template
    if 'pronoun' not in template:
        return phrase

    singular = False
    plural = False
    if 'pronoun-subj-s' in template:
        singular = True
    elif 'pronoun-subj-pl' in template:
        plural = True

    t = template

    if singular:
        gender = random.choice(['m', 'f'])
        if gender == 'm':
            t = t.replace('{pronoun-subj-s}', 'he')
            t = t.replace('{pronoun-obj}', 'him')
        else:
            t = t.replace('{pronoun-subj-s}', 'she')
            t = t.replace('{pronoun-obj}', 'her')
            
    elif plural:
        t = t.replace('{pronoun-subj-pl}', 'they')
        t = t.replace('{pronoun-obj}', 'them')

    else:
        gender = random.choice(['m', 'f', 'n'])
        if gender == 'm':
            t = t.replace('{pronoun-obj}', 'him')
        elif gender == 'f':
            t = t.replace('{pronoun-obj}', 'her')
        else:
            t = t.replace('{pronoun-obj}', 'them')
    t = t.replace('  ', ' ')
    return Phrase(t, phrase.parse.replace('  ', ' '), phrase.grammar)

def gen_phrases(grammar_file: str, num_examples: int) -> List[str]:
    grammar = yaml.safe_load(open(grammar_file))
    root_components = [Component(**obj) for obj in grammar['root']]
    all_components = root_components + [Component(**obj) for obj in grammar['components']]
    phrases = []
    for c in root_components:
        # print(c.name)
        series = (fill_pronouns(p) for p in c.enumerate())
        for i in range(1000):
            phrases.append(next(series))

    dataset = [{'sentence': p.template, 'parse': p.parse} for p in phrases]
    dataset = Dataset.from_list(dataset)
    def anonymize(x):
        sentence = x['sentence']
        parse = x['parse']
        for i, pattern in enumerate(re.findall(r'"(.*?)"', sentence)):
            sentence = sentence.replace(f'"{pattern}"', f'[phrase_{i}]')
            parse = parse.replace(f'"{pattern}"', f'[phrase_{i}]')
        x['sentence_anon'] = sentence
        x['parse_anon'] = parse
        return x

    dataset = dataset.map(anonymize).shuffle()
    dataset.save_to_disk('../data/dataset')
    

if __name__ == '__main__':
    gen_phrases('grammar.yaml', 50)