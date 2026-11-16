class BusinessError(Exception):
    status_code = 409
    field = None

    def __init__(self, message, field=None):
        super().__init__(message)
        self.message = message
        self.field = field


class NotFoundError(BusinessError):
    status_code = 404


class DuplicateError(BusinessError):
    status_code = 409


class InUseError(BusinessError):
    status_code = 409


class RuleViolationError(BusinessError):
    status_code = 409


class InvalidStateError(BusinessError):
    status_code = 409

