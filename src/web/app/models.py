from pydantic import BaseModel


class AuthModel(BaseModel):
    data_check_string: str
    hash: str


class IDsModel(BaseModel):
    uuid: str
    player_id: str


class ScoreModel(BaseModel):
    query_id: str
    uuid: str
    player_id: str
