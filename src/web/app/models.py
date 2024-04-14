from pydantic import BaseModel


class StatusModel(BaseModel):
    uuid: str


class AuthModel(BaseModel):
    data_check_string: str
    hash: str


class GameConnectionModel(BaseModel):
    player_id: int
    uuid: str
    query_id: str


class ScoreModel(BaseModel):
    score: int
