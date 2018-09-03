from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        import traceback

        print(traceback.format_exc())
