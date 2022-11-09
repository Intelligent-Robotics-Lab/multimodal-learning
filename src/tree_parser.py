import py_trees
from transformers import AutoTokenizer, AutoModelForTokenClassification, T5ForConditionalGeneration, T5Tokenizer
from transformers.pipelines.token_classification import TokenClassificationPipeline
import torch

class AnonymizationPipeline(TokenClassificationPipeline):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def postprocess(self, model_outputs, **kwargs):
        entities = super().postprocess(model_outputs, aggregation_strategy="first", **kwargs)
        result = ""
        substitution = ""
        substitutions = {}
        in_quote = False
        i = 0
        for entity in entities:
            if entity["entity_group"] == "LABEL_0":
                if in_quote:
                    result += f'phrase_{i} '
                    substitutions[f'[phrase_{i}]'] = substitution.strip()
                    substitution = ""
                    i += 1
                    in_quote = False
            elif entity["entity_group"] == "LABEL_1":
                if not in_quote:
                    in_quote = True
            if in_quote:
                substitution += entity["word"] + " "
            else:
                result += entity["word"] + " "
        if in_quote:
            result += f'[phrase_{i}] '
            substitutions[f'[phrase_{i}]'] = substitution.strip()
        return result, substitutions

class TextParser:
    def __init__(self):
        bert_tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        bert_model = AutoModelForTokenClassification.from_pretrained("../models/model")
        self.pipe = AnonymizationPipeline(model=bert_model, tokenizer=bert_tokenizer, device=0)
        self.tokenizer: T5Tokenizer = T5Tokenizer.from_pretrained("t5-base", model_max_length=128)
        self.model = T5ForConditionalGeneration.from_pretrained("../models/parse-model").to('cuda')
        self.custom_token_ids = self.tokenizer.encode('if(says([phrase_0]),say([phrase_1])) resolve() ask() say() label()', return_tensors='pt')

    def parse(self, sample: str):
        sentence_anon, subs = self.pipe(sample)
        model_inputs = self.tokenizer(
            sentence_anon,
            max_length=128,
            truncation=True,
            return_tensors="pt",
        )['input_ids']
        output_space = torch.cat([self.custom_token_ids, model_inputs], dim=1)
        unique = torch.unique(output_space, dim=1, sorted=False)
        def allowed_tokens_fn(batch_id, input_ids):
            return unique[batch_id]
        output_ids = self.model.generate(model_inputs.to('cuda'), max_length=30, prefix_allowed_tokens_fn=allowed_tokens_fn, num_beams=1)
        print(output_ids)
        parse = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        for key, value in subs.items():
            parse = parse.replace(key, value)
        return parse

if __name__ == '__main__':
    parser = TextParser()
    print(parser.parse("if they say sandwich then ask them what meat they would like"))
