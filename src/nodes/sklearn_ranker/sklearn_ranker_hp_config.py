def hp_config(hp: HP):
    from sklearn.feature_extraction.text import TfidfVectorizer
    top_k = hp.number_input(20)
    ngram_range = hp.select({'basic': (1, 3), 'expanded': (3, 8)}, default='basic')
    analyzer = hp.select(['word', 'char'], default='word')
    vectorizer = TfidfVectorizer(ngram_range=ngram_range, analyzer=analyzer, lowercase=True)