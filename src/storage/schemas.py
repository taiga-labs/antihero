from pydantic import BaseModel


class UserModel(BaseModel):
    telegram_id: int
    name: str


class NftModel(BaseModel):
    user_id: int
    address: str
    name_nft: str
    rare: int


class PlayerModel(BaseModel):
    nft_id: int


class GameModel(BaseModel):
    uuid: str
    player_l_id: int
    player_r_id: int
    start_time: int


class WithdrawModel(BaseModel):
    nft_address: str
    dst_address: str


class PlayerState(BaseModel):
    player_id: int
    score: int = 0
    attempts: int = 3
    in_game: bool = False


class GameState(BaseModel):
    player_l: PlayerState
    player_r: PlayerState
    start_time: int
    active: bool = False
