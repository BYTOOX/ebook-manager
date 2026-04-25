from pydantic import BaseModel


class EbookBase(BaseModel):
    title: str
    author: str = "Unknown"


class EbookCreate(EbookBase):
    filename: str


class EbookRead(EbookBase):
    id: int
    filename: str

    model_config = {"from_attributes": True}
