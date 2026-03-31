from __future__ import annotations


class ConversationError(Exception):
    pass


class ConfigurationError(ConversationError):
    pass


class RateLimitedError(ConversationError):
    pass


class UnauthorizedError(ConversationError):
    pass


class BackendUnavailableError(ConversationError):
    pass


class InvalidResponseError(ConversationError):
    pass

