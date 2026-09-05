from fastapi import HTTPException


class NotFoundError(HTTPException):
    def __init__(self, message: str = "Not found"):
        super().__init__(status_code=404, detail={"code": "NOT_FOUND", "message": message})


class UnauthorizedError(HTTPException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": message},
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(status_code=403, detail={"code": "FORBIDDEN", "message": message})


class ConflictError(HTTPException):
    def __init__(self, message: str = "Conflict"):
        super().__init__(status_code=409, detail={"code": "CONFLICT", "message": message})


class UnprocessableError(HTTPException):
    def __init__(self, message: str = "Unprocessable"):
        super().__init__(status_code=422, detail={"code": "UNPROCESSABLE", "message": message})
