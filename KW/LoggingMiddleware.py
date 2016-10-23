class ExceptionLoggingMiddleware(object):
    def process_exception(self, request, exception):
        import traceback
        print(traceback.format_exc())