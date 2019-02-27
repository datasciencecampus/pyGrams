import pandas as pd
import unittest
import numpy as np

from scripts.text_processing import LemmaTokenizer, StemTokenizer
from scripts.tfidf_wrapper import TFIDF
from scripts import FilePaths
from scripts.filter_terms import FilterTerms
from scripts.terms_graph import TermsGraph
from scripts.tfidf_mask import TfidfMask
from scripts.tfidf_reduce import TfidfReduce
from scripts.utils import utils


class TestGraph(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        num_ngrams = 50
        min_n = 2
        max_n = 3
        max_df=0.3

        df = pd.read_pickle(FilePaths.us_patents_random_1000_pickle_name)
        tfidf_obj = TFIDF(docs_df=df, ngram_range=(min_n, max_n), max_document_frequency=max_df,
                                 tokenizer=StemTokenizer(), text_header='abstract')

        doc_weights = list(np.ones(len(df)))

        # term weights - embeddings
        filter_output_obj = FilterTerms(tfidf_obj.feature_names, None)
        term_weights = filter_output_obj.ngrams_weights_vect

        tfidf_mask_obj = TfidfMask(tfidf_obj, doc_weights, norm_rows=False, max_ngram_length=max_n)
        tfidf_mask_obj.update_mask(doc_weights, term_weights)
        tfidf_mask = tfidf_mask_obj.tfidf_mask

        # mask the tfidf matrix
        tfidf_matrix = tfidf_obj.tfidf_matrix
        tfidf_masked = tfidf_mask.multiply(tfidf_matrix)
        tfidf_masked = utils.remove_all_null_rows(tfidf_masked)

        print(f'Processing TFIDF matrix of {tfidf_masked.shape[0]:,} / {tfidf_matrix.shape[0]:,} documents')

        cls.__tfidf_reduce_obj = TfidfReduce(tfidf_masked, tfidf_obj.feature_names)
        term_score_tuples = cls.__tfidf_reduce_obj.extract_ngrams_from_docset('sum')
        graph_obj = TermsGraph(term_score_tuples[:num_ngrams], cls.__tfidf_reduce_obj)
        graph = graph_obj.graph
        cls.__links = graph['links']
        cls.__nodes = graph['nodes']

    def test_num_nodes(self):
        self.assertEquals(50, len(self.__nodes))

    def test_num_links(self):
        self.assertEquals(437, len(self.__links))

    def test_terms_in_nodes(self):
        texts = [x['text'] for x in self.__nodes]

        self.assertIn('central portion', texts)
        self.assertIn('fluid commun', texts)
        self.assertIn('provid seed', texts)
        self.assertIn('gate line', texts)

        idx_1 = texts.index("central portion")
        idx_2 = texts.index("fluid commun")
        idx_3 = texts.index("provid seed")
        idx_4 = texts.index("gate line")

        self.assertAlmostEqual(0.04789344988324536,  self.__nodes[idx_1]['freq'])
        self.assertAlmostEqual(0.0297340319434382,   self.__nodes[idx_2]['freq'])
        self.assertAlmostEqual(0.018931255387502864, self.__nodes[idx_3]['freq'])
        self.assertAlmostEqual(0.07313170875401664,  self.__nodes[idx_4]['freq'])

    def test_terms_in_links(self):

        texts = [(x['source'], x['target']) for x in self.__links]

        link_1 = ('semiconductor substrat', 'diffus barrier materi')
        link_2 = ('pharmaceut composit', 'activ inhibit product')
        link_3 = ('central portion', 'convex outer surfac')
        link_4 = ('comput system', 'core network')

        self.assertIn(link_1, texts)
        self.assertIn(link_2, texts)
        self.assertIn(link_3, texts)
        self.assertIn(link_4, texts)

        idx_1 = texts.index(link_1)
        idx_2 = texts.index(link_2)
        idx_4 = texts.index(link_3)
        idx_3 = texts.index(link_4)

        self.assertAlmostEqual(0.10691489601359874, self.__links[idx_1]['size'])
        self.assertAlmostEqual(0.04812269536077638, self.__links [idx_2]['size'])
        self.assertAlmostEqual(0.15789374804194328, self.__links [idx_3]['size'])
        self.assertAlmostEqual(0.03486527718367498, self.__links[idx_4]['size'])




