class FastRecvSMSError(Exception):
    pass


class NoNumbersAvailable(FastRecvSMSError):
    pass


class InsufficientBalance(FastRecvSMSError):
    pass


class OrderNotFound(FastRecvSMSError):
    pass


class AuthenticationError(FastRecvSMSError):
    pass


class ProviderError(FastRecvSMSError):
    pass
