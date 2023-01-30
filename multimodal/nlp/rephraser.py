from transformers import GPTJForCausalLM, AutoTokenizer
import torch

def get_model():
    model = GPTJForCausalLM.from_pretrained("EleutherAI/gpt-j-6B", torch_dtype=torch.float16).to('cuda')
    tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
    return model, tokenizer

def rephrase(phrase, model, tokenizer):
    prompt = (
f'''The following are instructions to a store employee and his corresponding responses.
Instruction: Ask the customer whether they would like tea or coffee.
Response: "Would you like tea or coffee?"
Instruction: Ask them whether they would like help with their luggage.
Response: "Would you like help with your luggage?"
Instruction: {phrase}.
Response: '''
    )
    tokenized = tokenizer(prompt, return_tensors="pt").to('cuda')
    input_ids = tokenized['input_ids']
    attention_mask = tokenized['attention_mask']
    gen_tokens = model.generate(
        input_ids,
        attention_mask=attention_mask,
        do_sample=False,
        max_length=100,
        eos_token_id=198
    )
    gen_text: str = tokenizer.batch_decode(gen_tokens[:, input_ids.shape[1]:-1])[0]
    return gen_text.strip().strip('"').strip("?")