from typing import overload
import datasets
from transformers import AutoTokenizer
from tokenizers import Tokenizer
from transformers import DataCollatorForTokenClassification
from transformers import AutoModelForTokenClassification, TrainingArguments, Trainer
from transformers.pipelines.token_classification import TokenClassificationPipeline

def label_sentence(sentence: str):
    label = []
    filtered_ids = []
    inquote = False
    beginquote = False
    sentence = sentence.replace('.', '')
    sentence = sentence.replace('?', '')
    sentence = sentence.replace('!', '')
    sentence = sentence.replace(',', '')
    
    in_quote = False
    for word in sentence.split(' '):
        if word.startswith('"'):
            if not word.endswith('"'):
                in_quote = True
            label.append(1)
        elif word.endswith('"'):
            in_quote = False
            label.append(1)
        else:
            if in_quote:
                label.append(1)
            else:
                label.append(0)

    sentence = sentence.replace('"', '')
    return sentence, label
        

    # for t, i in zip(tokens, ids):
    #     if t == '"':
    #         if inquote:
    #             inquote = False
    #             label[-1] = 2
    #         else:
    #             inquote = True
    #             beginquote = True
    #     else:
    #         filtered_ids.append(i)
    #         if beginquote:
    #             label.append(1)
    #             beginquote = False
    #         else:
    #             label.append(0)

tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
dataset = datasets.load_from_disk('../data/dataset-split')

def preprocess(sample):
    sentence = sample['sentence']
    masked_sentence, label = label_sentence(sentence)
    tokenized_inputs = tokenizer(masked_sentence.split(' '), truncation=True, is_split_into_words=True)


    word_ids = tokenized_inputs.word_ids()  # Map tokens to their respective word.
    previous_word_idx = None
    label_ids = []
    for word_idx in word_ids:  # Set the special tokens to -100.
        if word_idx is None:
            label_ids.append(-100)
        elif word_idx != previous_word_idx:  # Only label the first token of a given word.
            label_ids.append(label[word_idx])
        else:
            label_ids.append(-100)
        previous_word_idx = word_idx

    tokenized_inputs["labels"] = label_ids
    tokenized_inputs["masked_sentence"] = masked_sentence
    return tokenized_inputs

    # tokenized_input = tokenizer(dataset[0]["sentence"])
# ids = tokenized_input["input_ids"]
# tokens = tokenizer.convert_ids_to_tokens(ids)
# print(label_sentence("if they said \"Oh, May, she's such a tattletale.\" then say to the customer \"I have a weakness for coffee.\""))

dataset = dataset.map(preprocess)

# for sentence in dataset['train']:
#     if sentence['sentence'].startswith('say to'):
#         print(sentence['sentence'])

# print(dataset[0])
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
model = AutoModelForTokenClassification.from_pretrained("bert-base-uncased", num_labels=4)
training_args = TrainingArguments(
    output_dir="../data/results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=128,
    per_device_eval_batch_size=128,
    num_train_epochs=4,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"].remove_columns(["sentence", "masked_sentence"]),
    eval_dataset=dataset["test"].remove_columns(["sentence", "masked_sentence"]),
    tokenizer=tokenizer,
    data_collator=data_collator,
)

trainer.train()
model.save_pretrained('../models/model')


class AnonymizationPipeline(TokenClassificationPipeline):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def postprocess(self, model_outputs, **kwargs):
        entities = super().postprocess(model_outputs, aggregation_strategy="first", **kwargs)
        result = ""
        in_quote = False
        for entity in entities:
            if entity["entity_group"] == "LABEL_0":
                if in_quote:
                    result += "\" "
                    in_quote = False
                result += entity["word"] + " "
            elif entity["entity_group"] == "LABEL_1":
                if not in_quote:
                    result += "\""
                    in_quote = True
                result += entity["word"] + " "
        if in_quote:
            result += "\""
        return result



pipe = AnonymizationPipeline(model=model, tokenizer=tokenizer, device=0)

# def postprocess(sample):
#     out = ""
#     for word in sample:
#         if word['entity'] == 'LABEL_0':
#             out += word['word'] + ' '
#     return tokenized_inputs

# print(dataset["test"][0]["masked_sentence"])
# print(pipe(dataset["test"][0]["masked_sentence"]))
# print(pipe("if the individual says they would like coffee then tell them okay great"))
print(pipe(["Say hello to the customer",
"ask them what they would like to order",
"if they say sandwich then ask them what meat they would like",
"next ask them whether they want cheese",
"ask them if they want any other toppings",
"then tell them to go to the payment counter",
"Say to the customer welcome to starbucks what can i get you",
"ask the customer how is your day going"]))