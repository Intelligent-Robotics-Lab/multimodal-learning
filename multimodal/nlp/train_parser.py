from typing import Any, Dict, List, Optional, Tuple, Union

import datasets
import evaluate
import numpy as np
import torch
from torch import nn
from transformers import (Seq2SeqTrainer, Seq2SeqTrainingArguments,
                          T5ForConditionalGeneration, T5Tokenizer)
from multimodal.data.dataset import get_dataset
from multimodal.utils import get_model_path

dataset = get_dataset().shuffle()
tokenizer: T5Tokenizer = T5Tokenizer.from_pretrained("t5-base", model_max_length=128)
model = T5ForConditionalGeneration.from_pretrained("t5-base")
custom_token_ids = tokenizer.encode('if(says([phrase_0]),say([phrase_1],ask([phrase_2]))) resolve() ask() say() label()', return_tensors='pt')

class ParserTrainer(Seq2SeqTrainer):
    def prediction_step(
        self,
        model: nn.Module,
        inputs: Dict[str, Union[torch.Tensor, Any]],
        prediction_loss_only: bool,
        ignore_keys: Optional[List[str]] = None,
    ) -> Tuple[Optional[float], Optional[torch.Tensor], Optional[torch.Tensor]]:
        # output_space = torch.concat([custom_token_ids, inputs['input_ids']], dim=1)
        batch_size = inputs['input_ids'].shape[0]
        output_space = torch.cat([custom_token_ids.repeat(batch_size, 1), inputs['input_ids']], dim=1)
        unique = torch.unique(output_space, dim=1, sorted=False)
        def allowed_tokens_fn(batch_id, input_ids):
            return unique[batch_id]

        self._gen_kwargs['prefix_allowed_tokens_fn'] = allowed_tokens_fn
        return super().prediction_step(model, inputs, prediction_loss_only, ignore_keys)

def preprocess(sample):
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
    return model_inputs

def prefix(sample):
    sample['sentence_anon'] = ' ' + sample['sentence_anon']
    return sample

dataset = dataset.map(preprocess, batched=True, batch_size=128, remove_columns=dataset.column_names['train'])
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
    result = metric.compute(predictions=decoded_preds, references=decoded_labels)
    return result

trainer = ParserTrainer(
    model=model,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    args=training_args,
    compute_metrics=compute_metrics
)
trainer.train()

model.save_pretrained(get_model_path('parse-model'))
