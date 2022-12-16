from importlib_resources import files, as_file

def get_model_path(name: str):
    model_path = files('multimodal') / 'models' / name
    with as_file(model_path) as p:
        return p