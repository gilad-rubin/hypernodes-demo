import ast
import os
import tempfile
from collections import defaultdict
from typing import Any, Dict, List

import hypster
import streamlit as st
from hamilton import driver
from hypster import HP
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowEdge, StreamlitFlowNode
from streamlit_flow.layouts import LayeredLayout, TreeLayout
from dotenv import load_dotenv
load_dotenv()
from src.hypernodes import HyperNode

st.set_page_config(page_title="RAG App Demo")

st.session_state["execute"] = 0
def format_title(title):
    title = title.replace("_", " ").replace(".", " ")
    words = title.split()
    formatted_words = [word.upper() if word.upper() in ['RAG', 'LLM', 'QA'] else word.capitalize() for word in words]
    return ' '.join(formatted_words)

def parse_hypster_config(modified_source):
    tree = ast.parse(modified_source)
    config_calls = []

    class ConfigVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "hp"
            ):
                method_name = node.func.attr
                if method_name in ["select", "text_input", "number_input"]:
                    args = [ast.literal_eval(arg) for arg in node.args]
                    kwargs = {
                        kw.arg: ast.literal_eval(kw.value) for kw in node.keywords
                    }
                    config_calls.append((method_name, args, kwargs))
            self.generic_visit(node)

    ConfigVisitor().visit(tree)
    return config_calls

def create_streamlit_widget(method_name, args, kwargs):
    name = kwargs.get("name")
    if not name:
        st.warning(f"No name provided for {method_name}. Using default.")
        name = method_name

    display_name = format_title(name)

    if method_name == "select":
        options = args[0] if args else kwargs.get("options", [])
        if isinstance(options, dict):
            options_list = list(options.keys())
            default = kwargs.get("default", options_list[0] if options_list else None)
            return st.selectbox(
                display_name,
                options_list,
                index=options_list.index(default) if default in options_list else 0,
                key=name,
            )
        elif isinstance(options, list):
            default = kwargs.get("default", options[0] if options else None)
            return st.selectbox(
                display_name,
                options,
                index=options.index(default) if default in options else 0,
                key=name,
            )
    elif method_name == "text_input":
        default = args[0] if args else kwargs.get("default", "")
        return st.text_input(display_name, value=default, key=name)
    elif method_name == "number_input":
        default = args[0] if args else kwargs.get("default", 0)
        value = default if isinstance(default, int) else float(default)
        return st.number_input(display_name, value=value, key=name)


def hamilton_to_streamlit_flow(hamilton_driver: driver.Driver) -> Dict[str, Any]:
    dag = hamilton_driver.graph

    nodes: List[StreamlitFlowNode] = []
    edges: List[StreamlitFlowEdge] = []

    # Group inputs by their target nodes
    input_groups = defaultdict(list)
    for node_name, node_obj in dag.nodes.items():
        if node_obj.user_defined:
            for dependent in node_obj.depended_on_by:
                input_groups[dependent.name].append(node_name)

    # Create nodes
    for node_name, node_obj in dag.nodes.items():
        if node_obj.user_defined:
            continue  # Skip individual input nodes, we'll create grouped ones later

        style = {
            "background": "#FFC857",
            "border": "2px solid #000000",
        }  # Yellow for non-input nodes

        nodes.append(
            StreamlitFlowNode(
                id=node_name,
                pos=(0, 0),
                data={"content": node_name},
                node_type="default",
                source_position="bottom",
                target_position="top",
                style=style,
                draggable=False,
            )
        )

    # Create grouped input nodes
    for target_node, inputs in input_groups.items():
        inputs = [format_title(input) for input in inputs]
        input_content = "\n\n".join(inputs)
        nodes.append(
            StreamlitFlowNode(
                id=f"input_{target_node}",
                pos=(0, 0),
                data={"content": input_content},
                node_type="input",
                source_position="bottom",
                target_position="top",
                style={
                    "background": "#ffffff",
                    "border": "2px solid #000000",
                },  # White for input nodes
                draggable=False,
            )
        )

        # Create edge from grouped input to target node
        edges.append(
            StreamlitFlowEdge(
                id=f"input_{target_node}-{target_node}",
                source=f"input_{target_node}",
                target=target_node,
                animated=True,
                style={"stroke": "#666666"},
            )
        )

    # Create edges between non-input nodes
    for node_name, node_obj in dag.nodes.items():
        if not node_obj.user_defined:
            for dep in node_obj.dependencies:
                if not dep.user_defined:
                    edges.append(
                        StreamlitFlowEdge(
                            id=f"{dep.name}-{node_name}",
                            source=dep.name,
                            target=node_name,
                            animated=True,
                            style={"stroke": "#666666"},
                        )
                    )

    # Create the Streamlit Flow component
    flow = streamlit_flow(
        key="hamilton_dag",
        init_nodes=nodes,
        init_edges=edges,
        layout=LayeredLayout(
            direction="down",
            horizontal_spacing=120,
            vertical_spacing=80,
            node_node_spacing=40,
            node_layer_spacing=60,
        ),
        fit_view=True,
        show_minimap=False,
        show_controls=False,
        pan_on_drag=False,
        allow_zoom=False,
        height=800,  # Increase overall height of the graph
    )

    return flow

import streamlit as st
from src.hypernodes import HyperNode
import hypster

def show_options(node):
    hypster_instance = node.hp_config
    _, hp_calls = hypster.ast_analyzer.analyze_hp_calls(hypster_instance.source_code)
    modified_source = hypster.ast_analyzer.inject_names(
        hypster_instance.source_code, hp_calls
    )
    return parse_hypster_config(modified_source)

def create_widgets_for_node(config_calls, prefix=""):
    for method_name, args, kwargs in config_calls:
        widget_key = f"{prefix}{kwargs.get('name', method_name)}"
        create_streamlit_widget(method_name, args, {**kwargs, 'name': widget_key})

def main():
    st.title("RAG App Execution")
    
    # Load Batch QA node
    batch_qa_node = HyperNode.load("src/nodes/batch_qa")
    batch_qa_config_calls = show_options(batch_qa_node)
    
    # Load RAG QA node
    rag_qa_node = HyperNode.load("src/nodes/rag_qa")
    rag_qa_config_calls = show_options(rag_qa_node)
    
    st.write("## Configuration Options")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Batch QA Configurations")
        create_widgets_for_node(batch_qa_config_calls, prefix="batch_qa_")
    
    with col2:
        st.write("### RAG QA Configurations")
        create_widgets_for_node(rag_qa_config_calls, prefix="rag_qa_")
    
    
    combined_config = {}
    if st.button("Execute"):
        #add one to state:
        st.session_state["execute"] = st.session_state.get("execute", 0) + 1
        
        # Collect configurations
        batch_qa_config = {
            kwargs.get('name', method_name): st.session_state.get(f"batch_qa_{kwargs.get('name', method_name)}", "")
            for method_name, args, kwargs in batch_qa_config_calls
        }
        
        rag_qa_config = {
            kwargs.get('name', method_name): st.session_state.get(f"rag_qa_{kwargs.get('name', method_name)}", "")
            for method_name, args, kwargs in rag_qa_config_calls
        }
        rag_qa_config = {f"rag_qa.{k}": v for k, v in rag_qa_config.items()}
        
        # Combine configurations
        combined_config = {**rag_qa_config, **batch_qa_config}
        
    # Use Batch QA node for execution (as in the original code)
    batch_qa_node.instantiate_inputs(overrides=combined_config, return_config_snapshot=True)
    expanded_config = batch_qa_node._instantiated_inputs
    batch_qa_node.init_driver()
    all_nodes = list(batch_qa_node._driver.graph.nodes.keys())
    flow = hamilton_to_streamlit_flow(batch_qa_node._driver)
    if st.session_state.get("execute", 0) > 0:
        results = batch_qa_node.execute(final_vars=all_nodes, inputs=batch_qa_node._instantiated_inputs)
        st.write("## Run Executed Successfully with configurations:")
        st.json(expanded_config)

if __name__ == "__main__":
    main()