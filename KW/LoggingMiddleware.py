from django.utils.deprecation import MiddlewareMixin
from rest_framework_tracking.mixins import LoggingMixin
import logging
logger = logging.getLogger(__name__)

class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        import traceback
        print(traceback.format_exc())


class RequestLoggingMixin(LoggingMixin):
    def handle_log(self):
        logger.info(self.log)
