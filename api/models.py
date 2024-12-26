from pydantic import BaseModel


class UserMessage(BaseModel):
    fname: str | None = None
    lname: str | None = None
    email: str | None = None
    reason: str | None = None
    message: str 
