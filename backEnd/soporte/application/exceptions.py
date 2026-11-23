class BusinessError(Exception):
    field = None

    def __init__(self, message, field=None):
        super().__init__(message)
        self.message = message
        self.field = field


class NotFoundError(BusinessError):
    pass


class DuplicateError(BusinessError):
    pass


class InUseError(BusinessError):
    pass


class RuleViolationError(BusinessError):
    pass


class InvalidStateError(BusinessError):
    pass

