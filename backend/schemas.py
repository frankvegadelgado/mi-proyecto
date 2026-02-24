from pydantic import BaseModel

# Schema para crear un item (entrada)
class ItemCreate(BaseModel):
    name: str
    description: str

# Schema para responder con un item (incluye id)
class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True  # Pydantic v2 (antes era orm_mode = True)