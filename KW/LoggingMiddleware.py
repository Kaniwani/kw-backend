from django.utils.deprecation import MiddlewareMixin


class ExceptionLoggingMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        import traceback
        print(traceback.format_exc())