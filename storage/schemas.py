from pydantic import BaseModel


class UserModel(BaseModel):
    telegram_id: int
    name: str


class NftModel(BaseModel):
    user_id: int
    address: str
    name_nft: str
    rare: int


class WithdrawModel(BaseModel):
    nft_address: str
    dst_address: str
