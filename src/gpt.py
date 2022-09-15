from time import time
from transformers import GPTJForCausalLM, AutoTokenizer
import torch

print("Loading model...")
model = GPTJForCausalLM.from_pretrained("EleutherAI/gpt-j-6B", torch_dtype=torch.float16).to('cuda')
print("Model loaded.")
tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")

prompt = (
    'Rephrase the following sentence: \
    Original: Ask the customer whether they would like tea or coffee. \
    New: The person says, "Would you like tea or coffee?" \
    Original: Ask the customer how their day is going. \
    New: The person says, "'
)
print("Tokenizing prompt...")
input_ids = tokenizer(prompt, return_tensors="pt").to('cuda').input_ids
print("Generating...")
start_time = time()
gen_tokens = model.generate(
    input_ids,
    temperature=0,
    max_length=100,
)
end_time = time()
print(f"Time to generate: {end_time - start_time}")
gen_text = tokenizer.batch_decode(gen_tokens)[0]
print(gen_text)