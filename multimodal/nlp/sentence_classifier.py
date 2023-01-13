import sentence_transformers
from enum import Enum
from multimodal.data.dataset import get_dataset
from multimodal.utils import get_model_path
from sklearn.neighbors import KNeighborsClassifier
from pickle import dump, load

yes_answers = ['yes', 'yeah', 'sure', 'ok', 'okay', 'yes I am ready', 'sounds good', 'I am', "yes I am", "I'm ready", 'let\'s go']
no_answers = ['no', 'not yet', 'not really', 'not quite', 'no I am not', 'no, give me a minute', 'give me a minute', 'I am not ready yet', "I'm not sure", "hang on", 'I would like a moment']
done_answers = ['all done', 'you are finished', 'then you are done', 'you are done', "that's all", "that's it", "there is no next step", "nothing", "no", "none"]
uncertain_answers = ["hmm", 'I don\'t know', 'I\'m not sure', 'let me think', 'give me a minute', 'hang on', 'wait a minute']
misrecocognized_answers = ["you misunderstood", "you misunderstood me", "that's not correct", "misrecognition", "that's not what I said", "I did not say that", "you misheard me"]

instructions = get_dataset()

ready_pairs = [(0, a) for a in yes_answers] + \
              [(1, a) for a in no_answers]
instruction_pairs = [(0, a) for a in done_answers] + \
                    [(1, a) for a in uncertain_answers] + \
                    [(2, a) for a in misrecocognized_answers] + \
                    [(3, i['sentence']) for i in instructions['train']]

def train():
    embedding_model = sentence_transformers.SentenceTransformer('all-mpnet-base-v2')
    ready_model = KNeighborsClassifier(n_neighbors=3, algorithm='brute', weights='distance', metric='cosine')
    instruction_model = KNeighborsClassifier(n_neighbors=5, weights='distance', metric='cosine')
    y, x = zip(*ready_pairs)
    x = embedding_model.encode(x)
    ready_model.fit(x, y)
    y, x = zip(*instruction_pairs)
    x = embedding_model.encode(x)
    instruction_model.fit(x, y)
    with open(get_model_path('ready_model.pkl'), 'wb') as f:
        dump(ready_model, f)
    with open(get_model_path('instruction_model.pkl'), 'wb') as f:
        dump(instruction_model, f)

class SentenceType(Enum):
    YES = 0
    NO = 1
    DONE = 2
    UNCERTAIN = 3
    MISRECOGNIZED = 4 
    INSTRUCTION = 5
    UNKNOWN = 6

class SentenceClassifier:
    def __init__(self):
        self.embedding_model = sentence_transformers.SentenceTransformer('all-mpnet-base-v2')
        self.ready_model = load(open(get_model_path('ready_model.pkl'), 'rb'))
        self.instruction_model = load(open(get_model_path('instruction_model.pkl'), 'rb'))
    
    def classify_ready(self, sentence: str):
        embedding = self.embedding_model.encode([sentence])
        y_pred = self.ready_model.predict_proba(embedding)
        score = y_pred.max()
        if score < 0.65:
            return SentenceType.UNKNOWN
        return SentenceType(y_pred.argmax())

    def classify_next(self, sentence: str):
        embedding = self.embedding_model.encode([sentence])
        y_pred = self.instruction_model.predict_proba(embedding)
        return SentenceType(y_pred.argmax() + 2)
    
if __name__ == '__main__':
    train()