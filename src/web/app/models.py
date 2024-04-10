from pydantic import BaseModel


class AuthModel(BaseModel):
    data_check_string: str
    hash: str


class IDsModel(BaseModel):
    uuid: str
    player_id: int


class StartModel(BaseModel):
    data_check_string: str
    hash: str
    uuid: str
    player_id: int


class ScoreModel(BaseModel):
    data_check_string: str
    hash: str
    query_id: str
    uuid: str
    player_id: int
    score: int
