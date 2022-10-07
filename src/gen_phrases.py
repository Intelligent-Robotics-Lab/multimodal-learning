from __future__ import annotations
from logging import root
import yaml
import datasets
import re
from itertools import cycle
from typing import Dict, Iterable, List

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

questions = cycle(load_questions().shuffle()["sentence"])
statements = cycle(load_statements().shuffle()["sentence"])
imperatives = cycle(load_imperatives().shuffle()["text"])

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

class Template:
    def __init__(self, template: str, parse: str, grammar: Dict):
        self.template = template
        self.parse = parse
        self.wildcards = [Wildcard(x) for x in re.findall('\{(.*?)\}', template)]
        self.grammar = grammar
        
    def replace(self, wildcard: Wildcard, replacement: str) -> str:
        # print(f'Replacing {wildcard} with {replacement}')
        # print(str(wildcard))
        new_template = self.template.replace(f'{str(wildcard)}', replacement, 1)
        # print(f'Old template: {self.template}')
        # print(f'New template: {new_template}')
        if wildcard.index is None:
            new_parse = self.parse
        else:
            new_parse = self.parse.replace(f'{{${wildcard.index}}}', replacement, 1)
        return Template(new_template, new_parse, self.grammar)

    def expand(self, recursion_depth=0) -> Iterable[Template]:
        # print(f'Expanding {self.template}, recursion depth {recursion_depth}')
        component_wildcards = [x for x in self.wildcards if not x.dynamic]
        base_wildcards = [x for x in self.wildcards if x.dynamic]
        if len(component_wildcards) == 0:
            # if len(base_wildcards) == 0:
            yield from cycle([self.template])
        elif component_wildcards
            # else:
                # pass
        else:
            component = self.grammar[component_wildcards[0].name]
            subbed_templates = (self.replace(component_wildcards[0], s) for s in component.enumerate())
            # having enumerated the first wildcard, we can now enumerate the rest
            enumerated_templates = cycle(t.expand(recursion_depth=recursion_depth+1) for t in subbed_templates)
            for t in enumerated_templates:
                x = next(t)
                # print(x)
                yield x

    # def expand(self, recursion_depth=0) -> Iterable[str]:
    #     # print(f'Expanding {self.template}, recursion depth {recursion_depth}')
    #     component_wildcards = [w for w in self.wildcards if w.split(':')[-1] not in dynamic_wildcards]
    #     base_wildcards = [w for w in self.wildcards if w.split(':')[-1] in dynamic_wildcards]
    #     if len(component_wildcards) == 0:
    #         if len(base_wildcards) == 0:
    #             yield from cycle([self.template])
    #         else:
    #             pass
    #     else:
    #         split_tag = component_wildcards[0].split(':')
    #         index, sub = split_tag if len(split_tag) == 2 else (None, split_tag[0])
    #         prefix = '' if index is None else f'{index}:'
    #         component = self.grammar[sub]
    #         subbed_templates = (self.template.replace(f'{{{component_wildcards[0]}}}', s, 1) for s in component.enumerate())
    #         # having enumerated the first wildcard, we can now enumerate the rest
    #         # print(list)
    #         # print(next(subbed_templates))
    #         enumerated_templates = cycle((Template(t, self.grammar).expand(recursion_depth=recursion_depth+1) for t in subbed_templates))
    #         for t in enumerated_templates:
    #             x = next(t)
    #             # print(x)
    #             yield x

class Component:
    registry = {}
    def __init__(self, name: str, parse: str, sentences: List[str]):
        self.name = name
        self.parse = parse
        self.sentences = sentences
        Component.registry[name] = self

    def __str__(self):
        return f'{self.name} ({self.parse}): {self.sentences}'

    def enumerate(self, num_examples: int = 1) -> Iterable[str]:
        templates = [Template(s, self.parse, Component.registry) for s in self.sentences]
        template_expansions = cycle((cycle(t.expand()) for t in templates))
        for t in template_expansions:
            yield next(t)
        # yield from cycle(template_expansions)
# def fill_template(grammar, sentence, num_examples: int) -> List[str]:
    

def gen_phrases(grammar_file: str, num_examples: int) -> List[str]:
    grammar = yaml.safe_load(open(grammar_file))
    root_components = [Component(**obj) for obj in grammar['root']]
    all_components = root_components + [Component(**obj) for obj in grammar['components']]
    for c in root_components:
        print(c.name)
        series = c.enumerate()
        for i in range(100):
            print(next(series))

if __name__ == '__main__':
    gen_phrases('grammar.yaml', 50)