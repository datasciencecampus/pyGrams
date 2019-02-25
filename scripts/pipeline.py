import scripts.data_factory as datafactory
import scripts.output_factory as output_factory
from scripts.documents_filter import DocumentsFilter
from scripts.documents_weights import DocumentsWeights
from scripts.filter_output_terms import FilterTerms
from scripts.text_processing import LemmaTokenizer
from scripts.tfidf_mask import TfidfMask
from scripts.tfidf_reduce import TfidfReduce
from scripts.tfidf_wrapper import TFIDF
from scripts.utils import utils


class Pipeline(object):
    def __init__(self, data_filename, docs_mask_dict,  pick_method='sum', max_n=3, min_n=1,
                 normalize_rows=False, text_header='abstract', term_counts=False, dates_header=None,
                 pickled_tf_idf=False,  time=False, citation_dict=None, nterms=25, max_df=0.1):
        # load data
        df = datafactory.get(data_filename)

        # calculate or fetch tf-idf mat
        if pickled_tf_idf:
            print('read from pickle')
            self.__tfidf_obj = None
        else:
            self.__tfidf_obj = TFIDF(docs_df=df, ngram_range=(min_n, max_n), max_document_frequency=max_df,
                                     tokenizer=LemmaTokenizer(), text_header=text_header)

        # docs weights( column, dates subset + time, citations etc.)
        doc_filters = DocumentsFilter(df, docs_mask_dict).doc_weights
        doc_weights = DocumentsWeights(df, time, citation_dict).weights
        doc_weights = [a * b for a, b in zip(doc_filters, doc_weights)]

        # term weights - embeddings
        filter_output_obj = FilterTerms(self.__tfidf_obj.feature_names, None)
        term_weights = filter_output_obj.ngrams_weights_vect

        # tfidf mask ( doc_ids, doc_weights, embeddings_filter will all merge to a single mask in the future)
        tfidf_mask_obj = TfidfMask(self.__tfidf_obj, doc_weights, norm_rows=normalize_rows, max_ngram_length=max_n)
        tfidf_mask_obj.update_mask(doc_weights, term_weights)
        tfidf_mask = tfidf_mask_obj.tfidf_mask

        # mask the tfidf matrix
        tfidf_matrix = self.__tfidf_obj.tfidf_matrix
        tfidf_masked = tfidf_mask.multiply(tfidf_matrix)
        tfidf_masked = utils.remove_all_null_rows(tfidf_masked)

        print(f'Processing TFIDF matrix of {tfidf_masked.shape[0]:,} / {tfidf_matrix.shape[0]:,} documents')

        self.__tfidf_reduce_obj = TfidfReduce(tfidf_masked, self.__tfidf_obj.feature_names)
        self.__term_counts_mat = None
        if term_counts:
            self.__term_counts_mat = self.__tfidf_reduce_obj.create_terms_count(df, dates_header)
        # if other outputs
        self.__term_score_tuples = self.__tfidf_reduce_obj.extract_nbest_from_mask( pick_method)


    def output(self, output_types, wordcloud_title=None, outname=None, nterms=50):
        for output_type in output_types:
            output_factory.create(output_type, self.__term_score_tuples, wordcloud_title=wordcloud_title,
                                  tfidf_reduce_obj=self.__tfidf_reduce_obj, name=outname,
                                  nterms=nterms, term_counts_mat=self.__term_counts_mat)