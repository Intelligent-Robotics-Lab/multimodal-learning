from py_trees.behaviour import Behaviour
from py_trees.trees import BehaviourTree
from transformers import AutoTokenizer, AutoModelForTokenClassification, T5ForConditionalGeneration, T5Tokenizer
from transformers.pipelines.token_classification import TokenClassificationPipeline
from multimodal.tasklearning.behaviours import CustomBehavior, Conditional, AskBehavior, SayBehavior, PersonSays
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
        if not sample:
            raise ValueError("Sample is empty")
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
        parse = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        print(parse)
        for key, value in subs.items():
            parse = parse.replace(key, value)
        return parse
    
class TreeParser(TextParser):    
    def _extract_fn(self, parse: str):
        function, body = parse.split('(', 1)
        assert body[-1] == ')'
        body = body[:-1]
        parentheses = 0
        result = ""
        arguments = []
        for char in body:
            if char == '(':
                parentheses += 1
            elif char == ')':
                parentheses -= 1
            if parentheses == 0:
                if char == ',':
                    arguments.append(result.strip())
                    result = ""
                    continue
            result += char
        arguments.append(result.strip())
        return function, arguments

    def append_tree(self, sample: str, tree: BehaviourTree = None, current_node: Behaviour = None):
        parse = self.parse(sample)
        fn, args = self._extract_fn(parse)
        if fn == 'resolve':
            b = CustomBehavior(name=args[0])
            if current_node:
                current_node.add_child(b)
            return b
        elif fn == 'if':
            precondition = self.append_tree(args[0])
            action = self.append_tree(args[1])
            b = Conditional(precondition, action)
            if tree is not None and current_node is not None:
                tree.add_child(b, current_node)
            return b
        elif fn == 'ask':
            b = AskBehavior(text=args[0])
            if current_node:
                current_node.add_child(b)
            return b
        elif fn == 'say':
            b = SayBehavior(text=args[0])
            if current_node:
                current_node.add_child(b)
            return b
        elif fn == 'says':
            b = PersonSays(text=args[0])
            if tree is not None and current_node is not None:
                if isinstance(current_node, Conditional) and len(current_node.children) == 0:
                    current_node.add_child(b)
                else:
                    raise ValueError("Says must be a child of a conditional")
            return b
        elif fn == 'label':
            b = CustomBehavior(name=args[0])
            if tree is not None and current_node is not None:
                b.add_child(current_node)
                if not tree.replace_subtree(current_node.id, b):
                    raise ValueError("Could not replace subtree")
            else:
                raise ValueError("Label requires an existing tree")
            return b


        
            

if __name__ == '__main__':
    parser = TreeParser()
    parse = parser.parse("if they say sandwich then ask them what meat they would like")
    print(parser._extract_fn(parse))
