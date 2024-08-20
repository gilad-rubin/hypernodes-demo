import streamlit as st
import ast
import tempfile
import os
import hypster
from hypster import HP

def parse_hypster_config(modified_source):
    tree = ast.parse(modified_source)
    config_calls = []

    class ConfigVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'hp':
                method_name = node.func.attr
                if method_name in ['select', 'text_input', 'number_input']:
                    args = [ast.literal_eval(arg) for arg in node.args]
                    kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords}
                    config_calls.append((method_name, args, kwargs))
            self.generic_visit(node)

    ConfigVisitor().visit(tree)
    return config_calls

def format_name(name):
    return name.replace("_", " ").replace(".", " - ").title()

def create_streamlit_widget(method_name, args, kwargs):
    name = kwargs.get('name')
    if not name:
        st.warning(f"No name provided for {method_name}. Using default.")
        name = method_name
    
    display_name = format_name(name)

    if method_name == 'select':
        options = args[0] if args else kwargs.get('options', [])
        if isinstance(options, dict):
            options_list = list(options.keys())
            default = kwargs.get('default', options_list[0] if options_list else None)
            return st.selectbox(display_name, options_list, index=options_list.index(default) if default in options_list else 0, key=name)
        elif isinstance(options, list):
            default = kwargs.get('default', options[0] if options else None)
            return st.selectbox(display_name, options, index=options.index(default) if default in options else 0, key=name)
    elif method_name == 'text_input':
        default = args[0] if args else kwargs.get('default', '')
        return st.text_input(display_name, value=default, key=name)
    elif method_name == 'number_input':
        default = args[0] if args else kwargs.get('default', 0)
        value = default if isinstance(default, int) else float(default)
        return st.number_input(display_name, value=value, key=name)

def main():
    st.title("Hypster Configuration Generator")

    uploaded_file = st.file_uploader("Upload your Hypster configuration file", type="py")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            hypster_instance = hypster.load(temp_file_path)
            _, hp_calls = hypster.ast_analyzer.analyze_hp_calls(hypster_instance.source_code)
            modified_source = hypster.ast_analyzer.inject_names(hypster_instance.source_code, hp_calls)
            
            config_calls = parse_hypster_config(modified_source)

            st.write("## Configuration Options")

            for method_name, args, kwargs in config_calls:
                create_streamlit_widget(method_name, args, kwargs)

            if st.button("Generate Configuration"):
                st.write("## Generated Configuration")
                config = {}
                for method_name, args, kwargs in config_calls:
                    name = kwargs.get('name', method_name)
                    config[name] = st.session_state[name]
                
                st.json(config)

        finally:
            os.unlink(temp_file_path)

if __name__ == "__main__":
    main()