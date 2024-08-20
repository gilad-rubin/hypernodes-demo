def hp_config(hp: HP):
    from src.hypernodes import HyperNode
    queries_path = hp.text_input('data/qa.xlsx')
    texts_path = hp.text_input('data/raw')
    base_path = 'src/nodes'
    rag_qa_node = HyperNode.load(f'{base_path}/rag_qa')
    rag_qa_node._instantiated_inputs = hp.propagate(rag_qa_node.hp_config, 'rag_qa')
    from hamilton.plugins.h_mlflow import MLFlowTracker
    from hamilton.driver import Builder
    adapters = []
    if hp.select([True, False], name='use_mlflow_adapter', default=True):
        mlflow_tracking_uri = hp.text_input('file:./mlruns')
        mlflow_adapter = MLFlowTracker(tracking_uri=mlflow_tracking_uri)
        adapters.append(mlflow_adapter)
    builder = Builder().with_adapters(*adapters)