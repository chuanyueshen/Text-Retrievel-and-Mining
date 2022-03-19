import math
import sys
import time

# =============================================================================
# import numpy as np
# import scipy.stats
# =============================================================================

import metapy
import pytoml

class InL2Ranker(metapy.index.RankingFunction):
    """
    Create a new ranking function in Python that can be used in MeTA.
    """
    def __init__(self, some_param=1.0):
        self.param = some_param
        # You *must* call the base class constructor here!
        super(InL2Ranker, self).__init__()

    def score_one(self, sd):
        """
        You need to override this function to return a score for a single term.
        For fields available in the score_data sd object,
        @see https://meta-toolkit.org/doxygen/structmeta_1_1index_1_1score__data.html
        """
        # doc_term_count = no. of times the term appears in current doc

        tfn = sd.doc_term_count * math.log(1.0 + sd.avg_dl/sd.doc_size,2)
        if tfn <= 0:
            return 0.0
        score = sd.query_term_weight * tfn/(tfn + self.param) * math.log((sd.num_docs + 1.0) / (sd.corpus_term_count + 0.5),2)
        return score


def load_ranker(cfg_file):
    """
    Use this function to return the Ranker object to evaluate, e.g. return InL2Ranker(some_param=1.0) 
    The parameter to this function, cfg_file, is the path to a
    configuration file used to load the index. You can ignore this for MP2.
    """
    return InL2Ranker(some_param=1) #metapy.index.JelinekMercer()

if __name__ == '__main__':
    '''
    if len(sys.argv) != 2:
        print("Usage: {} config.toml".format(sys.argv[0]))
        sys.exit(1)
    cfg = sys.argv[1]
    '''
    cfg = 'config.toml'
    print('Building or loading index...')
    idx = metapy.index.make_inverted_index(cfg)
    ranker = load_ranker(cfg)
    #ranker = metapy.index.OkapiBM25(k1=2.5, b=0.9, k3=500)
    '''
    b=0, MAP=0.228664178634
    b=0.1, MAP=0.233265672154
    b=0.2, MAP=0.240775256852
    b=0.25, MAP=0.243015581171
    b=0.3, MAP=0.246446146524
    b=0.4, MAP=0.248281376501
    b=0.5, MAP=0.250608568489
    b=0.6, MAP=0.253283907925
    b=0.7, MAP=0.25465606436
    b=0.75, MAP=0.255118673189
    b=0.8, MAP=0.256713971473
    b=0.9, MAP=0.256826592201
    b=1, MAP=0.257903268386, k=1.5
    
    b=1:
    k1=5, MAP=0.255601615296
    k1=10, MAP=0.244321082137
    k1=1, MAP=0.252902207385
    k1=2, MAP=0.260368707483 
    k1=3, MAP=0.259619151899
    k1=1.75, MAP=0.259393408639
    k1=2.5, MAP=0.261540019176
    
    k1=2.5, b=0.75, MAP=0.264553518239
    k1=2.5, b=0.9, MAP=0.267014557963 **
    '''
    ev = metapy.index.IREval(cfg)

    with open(cfg, 'r') as fin:
        cfg_d = pytoml.load(fin)

    query_cfg = cfg_d['query-runner']
    if query_cfg is None:
        print("query-runner table needed in {}".format(cfg))
        sys.exit(1)

    start_time = time.time()
    top_k = 10
    query_path = query_cfg.get('query-path', 'queries.txt')
    query_start = query_cfg.get('query-id-start', 0)

    query = metapy.index.Document()
    print('Running queries')
    avg_p_list = []
    with open(query_path) as query_file:
        for query_num, line in enumerate(query_file):
            query.content(line.strip())
            results = ranker.score(idx, query, top_k)
            avg_p = ev.avg_p(results, query_start + query_num, top_k)
            #avg_p_list.append(avg_p)
            print("Query {} average precision: {}".format(query_num + 1, avg_p))
    #np.savetxt('inl2.avg_p.txt', np.array(avg_p_list), fmt='%.12f')
    print("Mean average precision: {}".format(ev.map()))
    print("Elapsed: {} seconds".format(round(time.time() - start_time, 4)))

    
# =============================================================================
# bm25 = np.loadtxt('bm25.avg_p.txt',dtype='float32')
# inl2 = np.loadtxt('inl2.avg_p.txt',dtype='float32')
# stat, pval = scipy.stats.ttest_rel(bm25, inl2)
# np.savetxt('significance.txt', np.array([pval]), fmt='%.12f')
# =============================================================================
