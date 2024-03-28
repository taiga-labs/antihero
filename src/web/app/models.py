from pydantic import BaseModel


class AuthModel(BaseModel):
    data_check_string: str
    hash: str


class IDsModel(BaseModel):
    data_check_string: str
    hash: str


class ScoreModel(BaseModel):
    data_check_string: str
    hash: str
