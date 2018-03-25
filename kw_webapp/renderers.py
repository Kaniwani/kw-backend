
from rest_framework import renderers


class FallbackJSONRenderer(renderers.JSONRenderer):
    '''
    In order for all endpoints to return JSON, we use this renderer to automatically fill the an empty JSON response in
    cases where it would normally be null.
    '''
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            data = {"detail": "none"}
        return super().render(data, accepted_media_type, renderer_context)