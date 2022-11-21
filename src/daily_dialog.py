from datasets import load_dataset
from datasets.dataset_dict import DatasetDict
import re
import random
from typing import Dict, List
from lemminflect import getInflection

raw_dataset = load_dataset("daily_dialog")["train"]

def split_dialogs(batch):
    sentences = [s for sample in batch["dialog"] for s in sample if not re.search(r'[a-z]\.[A-Z]', s)]
    return {"turns": sentences}

def split_sentences(batch):
    sentences = [s for sample in batch["turns"] for s in re.split(r'(?<=(?<!\bMr)(?<!\bMs)(?<!\bMrs)(?<![A-HK-Z])[\.\!\?])\s+', sample)]
    return {"sentence": sentences}

def lowercase(sample):
    sample["sentence"] = sample["sentence"].lower()
    return sample

def normalize(sample):
    s = sample["turns"]
    s = re.sub(r' +', ' ', s)
    # s = re.sub(r'\.(?! )', '. ', s)
    s = s.replace(' ,', ',')
    s = s.replace(' .', '.')
    s = s.replace(' ?', '?')
    s = s.replace(' !', '!')
    s = s.replace('’', '\'')
    s = s.replace('‘', '\'')
    s = s.replace('“', '"')
    s = s.replace('”', '"')
    s = s.replace(' \' ', '\'')
    s = s.replace('p. m.', 'pm')
    s = s.replace('p.m.', 'pm ')
    s = s.replace('p. m', 'pm')
    s = s.replace('a. m.', 'am')
    s = s.replace('a.m.', 'am ')
    s = s.replace('a. m', 'am')
    # s = s.replace('"', '')
    s = s.strip()
    sample["turns"] = s
    return sample

def is_question(sample):
    first_word = sample["sentence"].split(' ')[0]
    return first_word in ['who', 'what', 'where', 'when', 'why', 'which', 'how', 'is', 'could', 'may', 'would', 'should', 'can', 'do', 'does', 'did', 'are', 'what\'s', 'will', 'have']

def is_do_question(sample):
    first_word, second_word = sample["sentence"].split(' ')[:2]
    return first_word == 'do' and second_word == 'you' and ',' not in sample["sentence"]

def third_person_inflect(sample):
    genders = ['he', 'she', 'they']
    gender = random.choice(genders)
    s: str = sample["sentence"]
    s = s.replace(" you ", f' {gender} ')
    if gender == 'they':
        s = s.replace(" your ", " their ")
        s = s.replace(" yourself", " themselves")
        s = s.replace(" yours", " theirs")
    elif gender == "he":
        s = s.replace(" your ", " his ")
        s = s.replace(" yourself", " himself")
        s = s.replace(" yours", " his")
    else:
        s = s.replace(" your ", " her ")
        s = s.replace(" yourself", " herself")
        s = s.replace(" yours", " hers")
    verb = s.split(' ')[2]
    if gender != 'they':
        s = s.replace(verb, getInflection(verb, 'VBZ')[0], 1)
    replacement = random.choice(['if', 'whether'])
    s = s.replace('do', replacement, 1)[:-1]
    sample["sentence"] = s
    return sample



dataset = raw_dataset
dataset = dataset.map(split_dialogs, batched=True, remove_columns=dataset.column_names)
dataset = dataset.map(normalize)
dataset = dataset.map(split_sentences, batched=True, remove_columns=dataset.column_names)
dataset = dataset.map(lowercase)
dataset = dataset.filter(lambda x: x["sentence"].count('"') == 0)
dataset = dataset.filter(lambda x: x["sentence"].count('?') + x["sentence"].count('.') + x["sentence"].count('!') <= 1)
questions = dataset.filter(lambda x: x["sentence"].endswith("?")).filter(is_question)
whether_questions = questions.filter(is_do_question).map(third_person_inflect)
statements = dataset.filter(lambda x: x["sentence"].endswith(".")).filter(lambda x: x["sentence"].count("...") == 0)
dataset = DatasetDict({"questions": questions, "statements": statements, "whether_questions": whether_questions})
dataset.save_to_disk("../data/daily_dialog")