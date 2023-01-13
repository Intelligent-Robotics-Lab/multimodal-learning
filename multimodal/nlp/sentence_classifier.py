import sentence_transformers
import torch
import datasets
from enum import Enum
from multimodal.data.dataset import get_dataset
from multimodal.utils import get_model_path
# from importlib_resources import files, as_file

yes_answers = ['yes', 'yeah', 'sure', 'ok', 'okay', 'yes I am ready', 'sounds good', 'I am', "yes I am", "I'm ready", 'let\'s go']
no_answers = ['no', 'not yet', 'not really', 'not quite', 'no I am not', 'no, give me a minute', 'give me a minute', 'I am not ready yet', "I'm not sure", "hang on", 'I would like a moment']
done_answers = ['all done', 'you are finished', 'then you are done', 'you are done', "that's all", "that's it", "there is no next step", "nothing", "no", "none"]
uncertain_answers = ["hmm", 'I don\'t know', 'I\'m not sure', 'let me think', 'give me a minute', 'hang on', 'wait a minute']
misrecocognized_answers = ["you misunderstood", "you misunderstood me", "that's not correct", "misrecognition", "that's not what I said", "I did not say that", "you misheard me"]

instructions = get_dataset() 

def train():
    batch_size = 64
    embedding_model = sentence_transformers.SentenceTransformer('all-mpnet-base-v2')
    yes_inputs = yes_answers * 100
    no_inputs = no_answers * 100
    done_inputs = done_answers * 100
    uncertain_inputs = uncertain_answers * 100
    misrecocognized_inputs = misrecocognized_answers * 100
    train_instructions = [ instruction['sentence'] for instruction in instructions['train']]
    test_instructions = [instruction['sentence'] for instruction in instructions['test']]
    yes_embeddings = embedding_model.encode(yes_inputs, convert_to_tensor=True)
    no_embeddings = embedding_model.encode(no_inputs, convert_to_tensor=True)
    done_embeddings = embedding_model.encode(done_inputs, convert_to_tensor=True)
    uncertain_embeddings = embedding_model.encode(uncertain_inputs, convert_to_tensor=True)
    misrecocognized_embeddings = embedding_model.encode(misrecocognized_inputs, convert_to_tensor=True)
    train_embeddings = embedding_model.encode(train_instructions, convert_to_tensor=True)
    test_embeddings = embedding_model.encode(test_instructions, convert_to_tensor=True)
    ready_train = torch.cat((yes_embeddings, no_embeddings))
    ready_test = ready_train
    ready_labels = [0] * len(yes_inputs) + [1] * len(no_inputs)
    instruction_train = torch.cat((done_embeddings, uncertain_embeddings, misrecocognized_embeddings, train_embeddings))
    instruction_test = torch.cat((done_embeddings, uncertain_embeddings, misrecocognized_embeddings, test_embeddings))
    instruction_labels = [0]  * len(done_inputs) + [1] * len(uncertain_inputs) + [2] * len(misrecocognized_embeddings) + [3] * len(train_instructions)
    instruction_test_labels = [0] * len(done_inputs) + [1] * len(uncertain_inputs) + [2] * len(misrecocognized_embeddings) + [3] * len(test_instructions)
    
    ready_train_ds = torch.utils.data.DataLoader(list(zip(ready_train, ready_labels)), batch_size=batch_size, shuffle=True)
    ready_test_ds = torch.utils.data.DataLoader(list(zip(ready_test , ready_labels)), batch_size=batch_size, shuffle=True)
    instruction_train_ds = torch.utils.data.DataLoader(list(zip(instruction_train, instruction_labels)), batch_size=batch_size, shuffle=True)
    instruction_test_ds = torch.utils.data.DataLoader(list(zip(instruction_test, instruction_test_labels)), batch_size=batch_size, shuffle=True)
    ready_model = torch.nn.Linear(768, 2).to('cuda')
    instruction_model = torch.nn.Linear(768, 4).to('cuda')
    def train_model(model, model_path, train_ds, test_ds): 
        loss_fn = torch.nn.CrossEntropyLoss()  
        optimizer = torch.optim.Adam(model.parameters(), lr=5e-5)
        dropout = torch.nn.Dropout(0.2)
        # optimizer = torch.optim.SGD(model.parameters(), lr=4e-3, weight_decay=1e-3)
        for i in range(200):
            train_loss = 0
            for x, l in train_ds:
                x = x.to('cuda')
                x += torch.randn_like(x) * 0.05
                l = l.to('cuda')
                # y = torch.nn.functional.one_hot(l).float().to('cuda')
                optimizer.zero_grad()
                y_pred = dropout(model(x))
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
                    x += torch.randn_like(x) * 0.05
                    l = l.to('cuda')
                    y_pred = model(x)
                    pred_class = torch.argmax(y_pred, dim=1)
                    correct += (pred_class == l).sum().item()
                    # for i in range(len(pred_class)):
                    #     if pred_class[i] != l[i]:
                    #         print(f'Prediction: {pred_class[i]} Actual: {l[i]}')
                    total += l.size(0)
            
            train_loss /= len(train_ds) * batch_size
            print('Epoch: {}. Loss: {}. Accuracy: {}'.format(i, train_loss, correct / total))
        torch.save(model.state_dict(), model_path)
    train_model(ready_model, get_model_path('ready_model.pt'), ready_train_ds, ready_test_ds)
    train_model(instruction_model, get_model_path('instruction_model.pt'), instruction_train_ds, instruction_test_ds)

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
        self.ready_model = torch.nn.Linear(768, 2).to('cuda')
        self.ready_model.load_state_dict(torch.load(get_model_path('ready_model.pt')))      
        self.ready_model.eval()
        self.instruction_model = torch.nn.Linear(768, 4).to('cuda')
        self.instruction_model.load_state_dict(torch.load(get_model_path('instruction_model.pt')))
        self.instruction_model.eval()
        self.embedding_model = sentence_transformers.SentenceTransformer('all-mpnet-base-v2')
    
    def classify_ready(self, sentence: str):
        embedding = self.embedding_model.encode(sentence, convert_to_tensor=True).to('cuda')
        y_pred = self.ready_model(embedding)
        y_pred = torch.nn.functional.softmax(y_pred, dim=0)
        score, pred_class = torch.max(y_pred, dim=0)
        if score < 0.7:
            return SentenceType.UNKNOWN
        return SentenceType(pred_class.item())

    def classify_next(self, sentence: str):
        embedding = self.embedding_model.encode(sentence, convert_to_tensor=True).to('cuda')
        y_pred = self.instruction_model(embedding)
        y_pred = torch.nn.functional.softmax(y_pred, dim=0)
        score, pred_class = torch.max(y_pred, dim=0)
        print(score, pred_class + 2)
        if score < 0.7:
            return SentenceType.UNKNOWN
        return SentenceType(pred_class.item() + 2)
    
if __name__ == '__main__':
    train()