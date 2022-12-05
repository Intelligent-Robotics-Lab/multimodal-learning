import sentence_transformers
import torch
import datasets
from enum import Enum

yes_answers = ['yes', 'yeah', 'sure', 'ok', 'okay', 'yes I am ready', 'sounds good', 'I am', "yes I am", "I'm ready", 'let\'s go']
no_answers = ['no', 'not yet', 'not really', 'not quite', 'no I am not', 'no, give me a minute', 'give me a minute', 'I am not ready yet', "I'm not sure", "hang on", 'I would like a moment']
done_answers = ['all done', 'you are finished', 'then you are done', 'you are done', "that's all", "that's it", "there is no next step", "nothing"]
uncertain_answers = ["hmm", 'I don\'t know', 'I\'m not sure', 'let me think', 'give me a minute']
instructions = datasets.load_from_disk('../data/dataset-split')

def train():
    batch_size = 16
    embedding_model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
    yes_inputs = [f'Are you ready? "{answer}"' for answer in yes_answers] * 100
    no_inputs = [f'Are you ready? "{answer}"' for answer in no_answers] * 100
    done_inputs = ['What should I do next? ' + answer for answer in done_answers] * 100
    uncertain_inputs = ['What should I do next? ' + answer for answer in uncertain_answers] * 100
    train_instructions = ['What should I do next? ' + instruction['sentence'] for instruction in instructions['train']]
    test_instructions = ['What should I do next? ' + instruction['sentence'] for instruction in instructions['test']]
    yes_embeddings = embedding_model.encode(yes_inputs, convert_to_tensor=True)
    no_embeddings = embedding_model.encode(no_inputs, convert_to_tensor=True)
    done_embeddings = embedding_model.encode(done_inputs, convert_to_tensor=True)
    uncertain_embeddings = embedding_model.encode(uncertain_inputs, convert_to_tensor=True)
    train_embeddings = embedding_model.encode(train_instructions, convert_to_tensor=True)
    test_embeddings = embedding_model.encode(test_instructions, convert_to_tensor=True)
    x_train = torch.cat((yes_embeddings, no_embeddings, done_embeddings, uncertain_embeddings, train_embeddings))
    x_train += torch.randn_like(x_train) * 0.1
    x_test = torch.cat((yes_embeddings, no_embeddings, done_embeddings, uncertain_embeddings, test_embeddings))
    train_labels = [0] * len(yes_inputs) + [1] * len(no_inputs) + [2] * len(done_inputs) + [3] * len(uncertain_inputs) + [4] * len(train_instructions)
    test_labels = [0] * len(yes_inputs) + [1] * len(no_inputs) + [2] * len(done_inputs) + [3] * len(uncertain_inputs) + [4] * len(test_instructions)
    train_ds = torch.utils.data.DataLoader(list(zip(x_train, train_labels)), batch_size=batch_size, shuffle=True)
    test_ds = torch.utils.data.DataLoader(list(zip(x_test, test_labels)), batch_size=batch_size, shuffle=True)
    model = torch.nn.Linear(384, 5).to('cuda')
    loss_fn = torch.nn.CrossEntropyLoss()   
    # optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-3)
    optimizer = torch.optim.SGD(model.parameters(), lr=4e-3, weight_decay=1e-3)
    for i in range(200):
        train_loss = 0
        for x, l in train_ds:
            x = x.to('cuda')
            l = l.to('cuda')
            # y = torch.nn.functional.one_hot(l).float().to('cuda')
            optimizer.zero_grad()
            y_pred = model(x)
            loss = loss_fn(y_pred, l)
            train_loss += loss.item() * batch_size
            loss.backward()
            optimizer.step()
        # Test the model
        with torch.no_grad():
            correct = 0
            total = 0
            for x, l in test_ds:
                x = x.to('cuda')
                l = l.to('cuda')
                y_pred = model(x)
                pred_class = torch.argmax(y_pred, dim=1)
                correct += (pred_class == l).sum().item()
                total += l.size(0)
        
        train_loss /= len(train_ds) * batch_size
        print('Epoch: {}. Loss: {}. Accuracy: {}'.format(i, train_loss, correct / total))
    torch.save(model.state_dict(), '../models/sentence-classifier.pt')

class SentenceType(Enum):
    YES = 0
    NO = 1
    DONE = 2
    UNCERTAIN = 3
    INSTRUCTION = 4 

class SentenceClassifier:
    def __init__(self):
        self.model = torch.nn.Linear(384, 5).to('cuda')
        self.model.load_state_dict(torch.load('../models/sentence-classifier.pt'))
        self.model.eval()
        self.embedding_model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
    
    def classify(self, sentence: str):
        embedding = self.embedding_model.encode(sentence, convert_to_tensor=True).to('cuda')
        y_pred = self.model(embedding)
        # compute softmax
        # print(y_pred)
        y_pred = torch.nn.functional.softmax(y_pred, dim=0)
        pred_class = torch.argmax(y_pred)
        return SentenceType(pred_class.item())
    
    def classify_ready(self, sentence: str):
        result = self.classify('Are you ready? ' + sentence)
        if result not in [SentenceType.YES, SentenceType.NO]:
            return SentenceType.UNCERTAIN
        return result

    def classify_next(self, sentence: str):
        result = self.classify('What should I do next? ' + sentence)
        if result not in [SentenceType.DONE, SentenceType.INSTRUCTION]:
            return SentenceType.UNCERTAIN
        return result
    
if __name__ == '__main__':
    train()