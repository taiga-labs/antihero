from pydantic import BaseModel


class UserModel(BaseModel):
    user_id: int
    name: str
    address: str


class NftModel(BaseModel):
    user_id: int
    address: str
    name_nft: str
    rare: str
