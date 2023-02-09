# import spacy
# from nltk import Tree

# nlp = spacy.load("en_core_web_sm")
# doc = nlp("ask the customer if they would like to check in")
# doc = nlp("ask the customer if they are checking in")
# for token in doc:
#     print(token.text, token.dep_, token.tag_, token.head.text, token.head.pos_,
#             [child for child in token.children])

# def to_nltk_tree(node):
#     if node.n_lefts + node.n_rights > 0:
#         return Tree(node.orth_, [to_nltk_tree(child) for child in node.children])
#     else:
#         return node.orth_


# [to_nltk_tree(sent.root).pretty_print() for sent in doc.sents]
# doc = nlp("ask the customer if they are checking in")
# for token in doc:
#     print(token.text, token.dep_, token.head.text, token.head.pos_, token.head.tag_,
#             [child for child in token.children])
import re

def inflect(phrase: str):
    result = re.sub(r'ask [a-z ]* (if|whether)\b they want', 'do you want', phrase)
    result = re.sub(r'ask\b[a-z ]*\b(if|whether)\b (he|she|the [a-zA-Z]*) wants', 'do you want', result)
    return result


test_strings = [
    "ask the customer if they want to check in",
    "ask him if he wants to check in",
    "ask whether the customer wants to check in"
    ]

print([inflect(s) for s in test_strings])