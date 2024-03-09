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
    exp_time: int


class WithdrawModel(BaseModel):
    nft_address: str
    dst_address: str
