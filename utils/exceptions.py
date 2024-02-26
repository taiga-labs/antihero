class ProviderFailed(Exception):
    def __init__(self, error_code):
        self.error_code = error_code
        super().__init__(f"Provider bid declined | error code: {error_code}")