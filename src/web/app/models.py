from pydantic import BaseModel


class AuthModel(BaseModel):
    data_check_string: str
    hash: str


class GameConnectionModel(BaseModel):
    player_id: int
    uuid: str


class ScoreModel(BaseModel):
    score: int
