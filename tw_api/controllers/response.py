# Response Api (RespApi)
from http.client import BAD_REQUEST, OK

API_VERSION = '/v1'

class ErrorResponse:
    def __init__(self, errCode='ERR', error=None, errorDescription=None):
        self.code = errCode
        self.error = error
        self.errorDescription = errorDescription


class Respapi:
    def __init__(self, data=None, code=None):
        self.data = data
        self.code = code

    def success(data):
        return Respapi(code=OK, data=data)

    def error(code=BAD_REQUEST, error="Error", errorDescription=None):
        if isinstance(error, tuple):
            return Respapi(code=code, data=ErrorResponse(errCode=error[0], error=error[1], errorDescription=error[2]).__dict__)
        return Respapi(code=code, data=ErrorResponse(error=error, errorDescription=errorDescription).__dict__)
