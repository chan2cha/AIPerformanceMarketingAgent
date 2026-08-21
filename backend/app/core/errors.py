from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    status_code: int
    code: str
    message: str


class AuthenticationError(AppError):
    def __init__(self, message: str = "인증이 필요합니다.") -> None:
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message)


class ResourceNotFoundError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(status_code=404, code=code, message=message)


class ServiceUnavailableError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(status_code=503, code=code, message=message)
