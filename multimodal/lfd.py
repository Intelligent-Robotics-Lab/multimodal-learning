import sentence_transformers
from multimodal.furhat import UserSpeech, SpeakerRole
from multimodal.utils import get_logger, get_data_path
from typing import AsyncGenerator
import pickle
import numpy as np

class LfD():
    def __init__(self, participant_id: str = '0'):
        self.embedding_model = sentence_transformers.SentenceTransformer('all-mpnet-base-v2')
        self.pairs = []
        self.logger = get_logger(f'LfD_{participant_id}')
        self.participant_id = participant_id
        self.actions = None
        self.states = None

    def save(self):
        path = get_data_path('lfd') / f'p_{self.participant_id}.pkl'
        with open(path, 'wb') as f:
            pickle.dump(self.pairs, f)

    def load(self):
        path = get_data_path('lfd') / f'p_{self.participant_id}.pkl'
        with open(path, 'rb') as f:
            self.pairs = pickle.load(f)
        self.vectorize()

    async def train(self, data: AsyncGenerator[UserSpeech, None]):
        state = None
        action = None
        self.pairs = []
        try:
            async for speech in data:
                if speech.role == SpeakerRole.CUSTOMER:
                    self.logger.info(f'Customer: {speech.text}')
                    if action is not None:
                        if state is None:
                            state = ''
                        self.pairs.append((state, action))
                        action = None
                        state = speech.text
                    elif state is None:
                        state = speech.text
                    else:
                        state = state + ' ' + speech.text
                elif speech.role == SpeakerRole.EMPLOYEE:
                    self.logger.info(f'Employee: {speech.text}')
                    if action is None:
                        action = speech.text
                    else:
                        action = action + ' ' + speech.text
        except StopAsyncIteration:
            if action is not None:
                if state is None:
                    state = ''
                self.pairs.append((state, action))

    def vectorize(self):
        states, actions = zip(*self.pairs)
        states = self.embedding_model.encode(states)
        actions = np.concatenate([np.zeros((1, 768)), self.embedding_model.encode(actions)[:-1]])
        self.actions = actions
        self.states = states

    def get_action(self, state: str, prev_action: str):
        if prev_action == '':
            action_embedding = np.zeros((1, 768))
        else:
            action_embedding = self.embedding_model.encode([prev_action])
        state_embedding = self.embedding_model.encode([state])
        dist = 0.8 * np.linalg.norm(self.states - state_embedding, axis=1) + 0.2 * np.linalg.norm(self.actions - action_embedding, axis=1)
        match_idx = np.argmin(dist)
        return self.pairs[match_idx][1], dist[match_idx]
        