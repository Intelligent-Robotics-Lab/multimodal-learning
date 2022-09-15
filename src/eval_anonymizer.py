from typing import overload
import datasets
from transformers import AutoTokenizer
from tokenizers import Tokenizer
from transformers import AutoModelForTokenClassification, TrainingArguments, Trainer
from transformers.pipelines.token_classification import TokenClassificationPipeline

tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")\

model = AutoModelForTokenClassification.from_pretrained("./model")

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
                    result = result[:-1] + "\" "
                    in_quote = False
                result += entity["word"] + " "
            elif entity["entity_group"] == "LABEL_1":
                if not in_quote:
                    result = result + "\""
                    in_quote = True
                result += entity["word"] + " "
        if in_quote:
            result = result[:-1] + "\""
        return result

pipe = AnonymizationPipeline(model=model, tokenizer=tokenizer, device=0)

print(pipe(["Say hello to the customer",
"ask them what they would like to order",
"if they say sandwich then ask them what meat they would like",
"next ask them whether they want cheese",
"ask them if they want any other toppings",
"then tell them to go to the payment counter",
"Say to the customer welcome to starbucks what can i get you",
"ask the customer how is your day going"]))