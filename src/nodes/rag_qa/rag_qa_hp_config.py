def hp_config(hp: HP):
    from src.hypernodes import HyperNode
    texts_path = hp.text_input('data/raw')
    query = hp.text_input("what's the document about?")
    chunker = hp.select(['paragraph', 'semantic', 'text'], default='paragraph')
    base_path = 'src/nodes'
    ranker_type = hp.select(['sklearn_ranker'], default='sklearn_ranker')
    ranker = HyperNode.load(f'{base_path}/{ranker_type}')
    ranker._instantiated_inputs = hp.propagate(ranker.hp_config, 'ranker')
    llm_model = hp.select({'mini': 'gpt-4o-mini', 'haiku': 'claude-3-haiku-20240307', 'sonnet': 'claude-3-5-sonnet-20240620', 'gpt-4o': 'gpt-4o', 'gpt-4o-latest': 'gpt-4o-2024-06-08'}, default='mini')
    llm_config = {'temperature': hp.number_input(0), 'max_tokens': hp.number_input(64)}
    system_prompt = hp.text_input('Answer with one word only')