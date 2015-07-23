"""
Doc2Vec wrapper that handles the more idiosyncratic aspects of implementing Gensim's Doc2Vec 
and also implements online testing as described in ...


"""

import numpy as np 
import gensim
from gensim.models.doc2vec import Doc2Vec, LabeledSentence, LabeledLineSentence
import re
import string
import Vectorizer

class Doc2Vec_Wrapper(Vectorizer):

    def __init__(self, size=300, window=8, min_count=2, workers=8):
        self.is_trained= False
        self.model = None

        self.size = size
        self.window = window
        self.min_count = min_count
        self.workers = workers

    def vectorize(self, docs):
        id2vector = {}

        unfound = []
        for item in docs:
            asset_id, _ = item
            label = 'DOC_' + str(asset_id)
            if label in self.model:
                id2vector.update({asset_id: self.model['DOC_' + str(asset_id)]})
            else:
                unfound.append(item)

        if len(unfound) > 0 :
            sentences = [self.gen_sentence(item) for item in unfound]
            self.update(sentences, train=False)
            vectors.update([self.model['DOC_' + str(item[0])] for item in unfound])

        return vectors

    def train(self, docs):
        train_sentences = [self.gen_sentence(item) for item in docs]
        if self.is_trained:
            ## online training 
            self.update(sentences, train=False)

        else:
            self.model = Doc2Vec(train_sentences, size=self.size, window=self.window, min_count=self.min_count, workers=self.workers)
            ## train from scratch
            self.is_trained = True

        return 'done training'

    def save_model(self, path):
        self.model.save(path)

    def _add_new_labels(self, sentences):
        sentence_no = -1
        total_words = 0
        vocab = self.model.vocab
        model_sentence_n = len([l for l in vocab if l.startswith("SENT")])
        n_sentences = 0
        for sentence_no, sentence in enumerate(sentences):
            sentence_length = len(sentence.words)
            for label in sentence.labels:
                total_words += 1
                if label in vocab:
                    vocab[label].count += sentence_length
                else:
                    vocab[label] = gensim.models.word2vec.Vocab(
                        count=sentence_length)

                    vocab[label].index = len(self.model.vocab) - 1
                    vocab[label].code = [0]
                    vocab[label].sample_probability = 1.
                    self.model.index2word.append(label)
                    n_sentences += 1
                    
        return n_sentences

    def _process(self, input):
        input = re.sub("<[^>]*>", " ", input) 
        punct = list(string.punctuation)
        for symbol in punct:
            input = input.replace(symbol, " %s " % symbol)
        input = filter(lambda x: x != u'', input.lower().split(' '))
        return input

    def _gen_sentence(self, assetid_body_tuple):
        '''
        assetid_body_tuple: 
            type tuple  
            param (assetid, bodytext) pair 
        '''
        asset_id, body = assetid_body_tuple
        text = self.process(body)
        sentence = LabeledSentence(text, labels=['DOC_%s' % asset_id])
        return sentence

        def update(self, sentences, train=False):
        n_sentences = self.add_new_labels(sentences)

        # add new rows to self.model.syn0
        n = self.model.syn0.shape[0]
        self.model.syn0 = np.vstack((
            self.model.syn0,
            np.empty((n_sentences, self.model.layer1_size), dtype=np.float32)
        ))

        for i in xrange(n, n + n_sentences):
            np.random.seed(
                np.uint32(self.model.hashfxn(self.model.index2word[i] + str(self.model.seed))))
            a = (np.random.rand(self.model.layer1_size) - 0.5) / self.model.layer1_size
            self.model.syn0[i] = a

        # Set self.model.train_words to False and self.model.train_labels to True
        self.model.train_words = train
        self.model.train_lbls = True

        # train
        self.model.train(sentences)
        return 


