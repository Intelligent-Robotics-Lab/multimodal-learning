from __future__ import annotations
from sklearn.utils import shuffle
import yaml
import datasets
from datasets import Dataset, concatenate_datasets
import re
from itertools import cycle
from typing import Dict, Iterable, List
import random
from lemminflect import getInflection
from importlib_resources import files, as_file

def get_dataset_path(name: str = 'dataset-split'):
    dataset_path = files('multimodal') / 'data' / name
    with as_file(dataset_path) as p:
        return p

def get_dataset(name: str = 'dataset-split'):
    dataset = datasets.load_from_disk(str(get_dataset_path(name)))
    return dataset

def preprocess(x):
    x['sentence'] = x['sentence'].lower()
    x['sentence'] = x['sentence'].split('.')[0]
    x['sentence'] = x['sentence'].replace('!', '')
    x['sentence'] = x['sentence'].replace(',', '')
    x['sentence'] = x['sentence'].replace('?', '')
    return x

def load_daily_dialog():
    dataset = get_dataset('daily_dialog')
    questions = dataset['questions']
    statements = dataset['statements']
    whether_questions = dataset['whether_questions']
    questions = questions.filter(lambda x: x['sentence'].count(' ') > 0 and x['sentence'].count('"') == 0)
    questions = questions.map(preprocess)
    statements = statements.filter(lambda x: x['sentence'].count(';') == 0 and x['sentence'].count('"') == 0)
    statements = statements.map(preprocess)
    whether_questions = whether_questions.filter(lambda x: x['sentence'].count(' ') > 0 and x['sentence'].count('"') == 0)
    whether_questions = whether_questions.map(preprocess)
    return questions, statements, whether_questions

def load_imperatives():
    dataset = datasets.load_dataset("text", data_files=str(get_dataset_path("imperatives.txt")))["train"]
    dataset = dataset.rename_column('text', 'sentence')
    dataset = dataset.map(preprocess)
    def filter_imperatives(x):
        return not (x['sentence'].startswith(('dont', 'don\'t', 'do ', 'let\'s', 'let us', 'if ', 'this ')) or ';' in x['sentence'] or '"' in x['sentence'] or '(' in x['sentence'])
    dataset = dataset.filter(filter_imperatives)
    return dataset

def load_actions():
    dataset = datasets.load_dataset("text", data_files=str(get_dataset_path("actions.txt")))["train"]
    dataset = dataset.rename_column('text', 'sentence')
    dataset = dataset.filter(lambda x: x['sentence'].count('"') == 0)
    dataset = dataset.map(preprocess)
    return dataset

"""
Algorithm:
Generate a tree of of components, excluding phrases
Lazy iterate through the tree, generating text where needed
"""

dynamic_wildcards = set(['phrase', 'question', 'imp', 'verb', 'gerund', 'pronoun-subj-s', 'pronoun-subj-pl', 'pronoun-obj'])

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
    def __init__(self, template: str, parse: str, grammar: Dict, vocab: Dict):
        self.template = template
        self.parse = parse
        self.wildcards = [Wildcard(x) for x in re.findall('\{(.*?)\}', template)]
        self.grammar = grammar
        self.vocab = vocab

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
        if wildcard.index is None:
            new_parse = self.parse
        else:
            new_parse = self.parse.replace(wildcard.index, sub_parse, 1)

        return Phrase(new_template, new_parse, self.grammar, self.vocab)

    def expand(self, recursion_depth=0) -> Iterable[Phrase]:
        # print(f'Expanding {self.template}, recursion depth {recursion_depth}')
        def get_replacements(wildcard: Wildcard) -> Iterable[Phrase]:
            if wildcard.dynamic:
                if wildcard.name == 'imp':
                    yield from (f'"{s}"' for s in self.vocab["imperatives"])
                elif wildcard.name == 'question':
                    yield from (f'"{s}"' for s in self.vocab["questions"])
                elif wildcard.name == 'phrase':
                    yield from (f'"{s}"' for s in self.vocab["statements"])
                elif wildcard.name == 'verb':
                    yield from (f' {s}' for s in self.vocab["actions"])
                elif wildcard.name == 'gerund':
                    yield from (f' {s}' for s in self.vocab["gerunds"])
                else:
                    yield from cycle([self])
            else:
                component = self.grammar[wildcard.name]
                yield from component.enumerate(recursion_depth=recursion_depth)
        
        replacements = [get_replacements(wildcard) for wildcard in self.wildcards]
        while True:
            phrase = self
            # print("Subbing:")
            # print(phrase)
            for i, wildcard in enumerate(self.wildcards):
                replacement = next(replacements[i])
                # print(f'Phrase: {phrase} wildcard: {wildcard.name} replacement: {replacement}')
                phrase = phrase.replace(wildcard, replacement)
                # print(f'Index {i}: {phrase}')
            yield phrase

class Component:
    registry = {}
    def __init__(self, name: str, parse: str, sentences: List[str], vocab: Dict):
        self.name = name
        self.parse = parse
        self.sentences = sentences
        self.vocab = vocab
        Component.registry[name] = self

    def __str__(self):
        return f'{self.name} ({self.parse}): {self.sentences}'

    def enumerate(self, num_examples: int = 1, recursion_depth=0) -> Iterable[str]:
        templates = [Phrase(s, self.parse, Component.registry, self.vocab) for s in self.sentences]
        template_expansions = [(t.expand(recursion_depth=recursion_depth+1)) for t in templates]
        # print(len(template_expansions))
        while True:
            for i, t in enumerate(template_expansions):
                n = next(t)
                # if recursion_depth == 1:
                # print(f'depth = {recursion_depth}, n = {n}')
                yield n
            # print('done')

def strip(phrase: Phrase) -> Phrase:
    return Phrase(phrase.template.replace('  ', ' ').strip(), phrase.parse.replace('  ', ' '), phrase.grammar, phrase.vocab)

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

    return Phrase(t, phrase.parse, phrase.grammar, phrase.vocab)

def gen_phrases(grammar_file: str, num_examples: int, vocab: Dict) -> List[str]:
    grammar = yaml.safe_load(open(grammar_file))
    root_components = [Component(**obj, vocab=vocab) for obj in grammar['root']]
    all_components = root_components + [Component(**obj, vocab=vocab) for obj in grammar['components']]
    phrases = []
    for c in root_components:
        # print(c.name)
        series = (fill_pronouns(p) for p in c.enumerate())
        series = (strip(p) for p in series)
        for i in range(num_examples // len(root_components)):
            phrases.append(next(series))
            # print(phrases[-1])

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
    return dataset
    

if __name__ == '__main__':
    questions, statements, whether_questions = load_daily_dialog()
    questions = questions.shuffle(seed=1).train_test_split(test_size=0.2)
    statements = statements.shuffle(seed=1).train_test_split(test_size=0.2)
    whether_questions = whether_questions.shuffle(seed=1).train_test_split(test_size=0.2)
    imperatives = load_imperatives().shuffle(seed=1).train_test_split(test_size=0.2)
    actions = load_actions().shuffle(seed=1).train_test_split(test_size=0.2)
    def inflect(x):
        first_word = x['sentence'].split(' ')[0]
        gerund = getInflection(first_word, tag='VBG')[0]
        x['sentence'] = x['sentence'].replace(first_word, gerund, 1)
        return x

    def combine_iters(x, y):
        while True:
            yield next(x)
            yield next(y)

    gerunds = actions.map(inflect)    

    train_vocab  = {
        'questions': combine_iters(cycle(questions['train']['sentence']), cycle(whether_questions['train']['sentence'])),
        'statements': cycle(statements['train']['sentence']),
        'imperatives': cycle(imperatives['train']['sentence']),
        'actions': cycle(actions['train']['sentence']),
        'gerunds': cycle(gerunds['train']['sentence']),
    }

    test_vocab  = {
        'questions': cycle(questions['test']['sentence']),
        'statements': cycle(statements['test']['sentence']),
        'imperatives': cycle(imperatives['test']['sentence']),
        'actions': cycle(actions['test']['sentence']),
        'gerunds': cycle(gerunds['test']['sentence']),
    }

    train_ds = gen_phrases(get_dataset_path('grammar.yaml'), 10000, train_vocab)
    for sample in list(train_ds)[:100]:
        print(sample["sentence"])
        print(sample["parse"])
    test_ds = gen_phrases(get_dataset_path('grammar.yaml'), 1000, test_vocab)

    dataset = datasets.DatasetDict({'train': train_ds, 'test': test_ds})
    dataset.save_to_disk(get_dataset_path('dataset-split'))