from transformers import GPTJForCausalLM, AutoTokenizer
import torch

class Rephraser:
    def __init__(self):
        print("Loading GPT model...")
        self.model = GPTJForCausalLM.from_pretrained("EleutherAI/gpt-j-6B", torch_dtype=torch.float16).to('cuda')
        print("Done loading GPT model")
        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")

    def rephrase_ask(self, phrase):
        prompt = (
f'''The following are instructions telling a store employee what to say to a customer and his corresponding responses.
Instruction: Ask the customer whether they would like tea or coffee.
Response: "Would you like tea or coffee?"
Instruction: Ask them if they would like help with their luggage.
Response: "Would you like help with your luggage?"
Instruction: {phrase}.
Response: '''
        )
        tokenized = self.tokenizer(prompt, return_tensors="pt").to('cuda')
        input_ids = tokenized['input_ids']
        attention_mask = tokenized['attention_mask']
        gen_tokens = self.model.generate(
            input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            max_length=200,
            eos_token_id=198
        )
        gen_text: str = self.tokenizer.batch_decode(gen_tokens[:, input_ids.shape[1]:-1])[0]
        return gen_text.strip().strip('"').strip("?")
    
    def rephrase_tell(self, phrase):
        prompt = (
f'''The following are instructions telling a store employee what to say to a customer and his corresponding responses. 
Instruction: Tell them that you cannot give them their order but your coworker can.
Response: "I cannot give you your order but my coworker can."
Instruction: Tell them that they can pick their order up at the counter.
Response: "You can pick your order up at the counter."
Instruction: {phrase}.
Response: '''
        )
        tokenized = self.tokenizer(prompt, return_tensors="pt").to('cuda')
        input_ids = tokenized['input_ids']
        attention_mask = tokenized['attention_mask']
        gen_tokens = self.model.generate(
            input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            max_length=200,
            eos_token_id=198
        )
        gen_text: str = self.tokenizer.batch_decode(gen_tokens[:, input_ids.shape[1]:-1])[0]
        return gen_text.strip().strip('"').strip(".")