from os import pread
import datasets
import evaluate
import numpy as np
# from transformers import AutoTokenizer
# from tokenizers import Tokenizer
# from transformers import DataCollatorForTokenClassification
from transformers import T5Tokenizer, T5ForConditionalGeneration, Seq2SeqTrainingArguments, Seq2SeqTrainer, AutoConfig, AutoTokenizer, AutoModelForSeq2SeqLM
from transformers.pipelines.token_classification import TokenClassificationPipeline
# from transformers import BartTokenizer, BartForConditionalGeneration
# from transformers import Trainer, TrainingArguments
# from transformers.modeling_bart import shift_tokens_right
# def label_sentence(sentence: str):
#     label = []
#     filtered_ids = []
#     inquote = False
#     beginquote = False
#     sentence = sentence.replace('.', '')
#     sentence = sentence.replace('?', '')
#     sentence = sentence.replace('!', '')
#     sentence = sentence.replace(',', '')
    
#     in_quote = False
#     for word in sentence.split(' '):
#         if word.startswith('"'):
#             if not word.endswith('"'):
#                 in_quote = True
#             label.append(1)
#         elif word.endswith('"'):
#             in_quote = False
#             label.append(1)
#         else:
#             if in_quote:
#                 label.append(1)
#             else:
#                 label.append(0)

#     sentence = sentence.replace('"', '')
#     return sentence, label
        

#     # for t, i in zip(tokens, ids):
#     #     if t == '"':
#     #         if inquote:
#     #             inquote = False
#     #             label[-1] = 2
#     #         else:
#     #             inquote = True
#     #             beginquote = True
#     #     else:
#     #         filtered_ids.append(i)
#     #         if beginquote:
#     #             label.append(1)
#     #             beginquote = False
#     #         else:
#     #             label.append(0)

# tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
dataset = datasets.load_from_disk('../data/dataset').shuffle()
for sample in dataset:
    if '"' in sample['parse_anon']:
        print(sample['parse_anon'])
        print(sample['sentence_anon'])
        print(sample['parse'])
        print(sample['sentence'])
        break
# config = AutoConfig.from_pretrained(
#     't5-small'
# )
# tokenizer = AutoTokenizer.from_pretrained(
#     't5-small'
# )
# model = AutoModelForSeq2SeqLM.from_pretrained(
#     't5-small',
#     config=config,
# )
tokenizer = T5Tokenizer.from_pretrained("t5-base", model_max_length=128)
model = T5ForConditionalGeneration.from_pretrained("t5-base")

# print(f"tokenized: {tokenizer.tokenize(text_target=dataset['sentence_anon'][0])}")

def preprocess(sample):
    # print(sample['sentence'])
    # print(sample['sentence_anon'])
    # print(sample['parse'])
    # print(sample['parse_anon'])
    # print(sample)
    # sample["parse_anon"] = '((Hello))'
    model_inputs = tokenizer(
        sample['sentence_anon'],
        padding="max_length",
        max_length=128,
        truncation=True,
        return_tensors="pt",
    )

    labels = tokenizer(
        sample['parse_anon'], 
        max_length=128, 
        padding="max_length", 
        truncation=True,
        return_tensors="pt",
    )
    label_ids = labels["input_ids"]
    label_ids[label_ids == tokenizer.pad_token_id] = -100

    model_inputs["labels"] = label_ids
    # for k, v in model_inputs.items():
    #     print(k, v.shape)
    return model_inputs

def test_parse(x):
    x['parse_anon'] = 'if(says([phrase_0]),say([phrase_1]))'
    return x

# dataset = dataset.map(test_parse)
dataset = dataset.map(preprocess, batched=True, batch_size=128)
dataset = dataset.train_test_split(test_size=0.9)
train_ds = dataset['train']
val_ds = dataset['test']

training_args = Seq2SeqTrainingArguments(
    output_dir="../data/parser-results",
    evaluation_strategy="epoch",
    learning_rate=3e-4,
    per_device_train_batch_size=64,
    per_device_eval_batch_size=64,
    num_train_epochs=5,
    predict_with_generate=True,
    generation_max_length=30,
)

metric = evaluate.load("exact_match")
def exact_match(eval_result):
    preds, labels = eval_result
    preds = preds[0]
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    


def compute_metrics(eval_preds):
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    for pred, label, dpred, dlabel in zip(preds, labels, decoded_preds, decoded_labels):
        if dlabel != dpred:
            print(f'pred: {dpred}, label: {dlabel}')
            # print(f'pred: {tokenizer.convert_ids_to_tokens(pred)}, label: {tokenizer.convert_ids_to_tokens(label)}')
    result = metric.compute(predictions=decoded_preds, references=decoded_labels)

    # prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
    # result["gen_len"] = np.mean(prediction_lens)
    # result = {k: round(v, 4) for k, v in result.items()}
    return result

trainer = Seq2SeqTrainer(
    model=model,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    args=training_args,
    compute_metrics=compute_metrics
    # tokenizer=tokenizer,
)
# print(train_ds[0]['input_ids'])
trainer.predict(train_ds.select([0]), temperature=0.0)
trainer.train()
# trainer.predict(val_ds.select(range(10)))
#     # tokenized_input = tokenizer(dataset[0]["sentence"])
# # ids = tokenized_input["input_ids"]
# # tokens = tokenizer.convert_ids_to_tokens(ids)
# # print(label_sentence("if they said \"Oh, May, she's such a tattletale.\" then say to the customer \"I have a weakness for coffee.\""))

# dataset = dataset.map(preprocess).train_test_split(test_size=0.1)
# # print(dataset[0])
# data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
# model = AutoModelForTokenClassification.from_pretrained("bert-base-uncased", num_labels=4)
# training_args = TrainingArguments(
#     output_dir="../data/results",
#     evaluation_strategy="epoch",
#     learning_rate=2e-5,
#     per_device_train_batch_size=16,
#     per_device_eval_batch_size=16,
#     num_train_epochs=2,
#     weight_decay=0.01,
# )

# trainer = Trainer(
#     model=model,
#     args=training_args,
#     train_dataset=dataset["train"].remove_columns(["sentence", "masked_sentence"]),
#     eval_dataset=dataset["test"].remove_columns(["sentence", "masked_sentence"]),
#     tokenizer=tokenizer,
#     data_collator=data_collator,
# )

# trainer.train()
# model.save_pretrained('../data/model')


# class AnonymizationPipeline(TokenClassificationPipeline):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)

#     def postprocess(self, model_outputs, **kwargs):
#         entities = super().postprocess(model_outputs, aggregation_strategy="first", **kwargs)
#         result = ""
#         in_quote = False
#         for entity in entities:
#             if entity["entity_group"] == "LABEL_0":
#                 if in_quote:
#                     result += "\" "
#                     in_quote = False
#                 result += entity["word"] + " "
#             elif entity["entity_group"] == "LABEL_1":
#                 if not in_quote:
#                     result += "\""
#                     in_quote = True
#                 result += entity["word"] + " "
#         if in_quote:
#             result += "\""
#         return result



# pipe = TokenClassificationPipeline(model=model, tokenizer=tokenizer, device=0)

# # def postprocess(sample):
# #     out = ""
# #     for word in sample:
# #         if word['entity'] == 'LABEL_0':
# #             out += word['word'] + ' '
# #     return tokenized_inputs

# # print(dataset["test"][0]["masked_sentence"])
# # print(pipe(dataset["test"][0]["masked_sentence"]))
# # print(pipe("if the individual says they would like coffee then tell them okay great"))
# print(pipe(["Say hello to the customer",
# "ask them what they would like to order",
# "if they say sandwich then ask them what meat they would like",
# "next ask them whether they want cheese",
# "ask them if they want any other toppings",
# "then tell them to go to the payment counter",
# "Say to the customer welcome to starbucks what can i get you",
# "ask the customer how is your day going"]))