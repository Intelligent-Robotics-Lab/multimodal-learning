from datasets import load_dataset
import re
from typing import Dict, List

raw_dataset = load_dataset("daily_dialog")["train"]

def split_dialogs(batch):
    sentences = [s for sample in batch["dialog"] for s in sample if not re.search(r'[a-z]\.[A-Z]', s)]
    return {"turns": sentences}

def split_sentences(batch):
    sentences = [s for sample in batch["turns"] for s in re.split(r'(?<=(?<!\bMr)(?<!\bMs)(?<!\bMrs)(?<![A-HK-Z])[\.\!\?])\s+', sample)]
    return {"sentence": sentences}

def fix_spaces(sample):
    s = sample["turns"]
    s = re.sub(r' +', ' ', s)
    # s = re.sub(r'\.(?! )', '. ', s)
    s = s.replace(' ,', ',')
    s = s.replace(' .', '.')
    s = s.replace(' ?', '?')
    s = s.replace(' !', '!')
    s = s.replace('’', '\'')
    s = s.replace('‘', '\'')
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

dataset = raw_dataset
dataset = dataset.map(split_dialogs, batched=True, remove_columns=dataset.column_names)
dataset = dataset.map(fix_spaces)
dataset = dataset.map(split_sentences, batched=True, remove_columns=dataset.column_names)
questions = dataset.filter(lambda x: x["sentence"].endswith("?"))
statements = dataset.filter(lambda x: x["sentence"].endswith("."))
print("Questions:", len(questions), " Statements:", len(statements))
questions.save_to_disk("../data/daily_dialog_questions")
statements.save_to_disk("../data/daily_dialog_statements")
questions.to_csv("../data/daily_dialog_questions.csv")
statements.to_csv("../data/daily_dialog_statements.csv")
with open("test.txt", 'w+') as f:
    for s in statements["sentence"]:
        f.write(s + "\n")