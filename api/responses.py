from rest_framework.response import Response


class InvalidWanikaniAPIKeyResponse(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 400
        self.data = {
            "error": "This Wanikani API Key is invalid! Check your settings page."
        }
