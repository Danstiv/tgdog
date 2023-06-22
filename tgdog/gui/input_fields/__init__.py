class InputField:

    def __init__(self, text=None, method_name=None):
        self.text = text
        self.method_name = method_name or 'process_{name}'

    # Validation probably will be implemented here later
