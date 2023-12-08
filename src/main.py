from datetime import datetime
from enum import Enum
from typing import List, Optional, Annotated, Union
from envparse import Env
from fastapi import APIRouter, FastAPI, Depends
from fastapi_users import FastAPIUsers
from pydantic import BaseModel, Field

from auth.auth import auth_backend
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate

env = Env()

fake_users = [
    {"id": 1, "role": "admin", "name": "Bob"},
    {"id": 2, "role": "investor", "name": "John", "degree": [
        {"id": 1, "created_at": "2020-01-01T00:00:00", "type_degree": "expert"}
    ]}
]
fake_trades = [
    {"id": 1, "user_id": 1, "currency": "BTC", "side": "buy", "price": 125, "amount": 2.15},
    {"id": 2, "user_id": 1, "currency": "BTC", "side": "sell", "price": 112, "amount": 2.15}
]



class DegreeType(Enum):
    newbie = "newbie"
    expert = "expert"


class Degree(BaseModel):
    id: int
    created_at: datetime
    type_degree: DegreeType  # (валидация) ждем только то, что описано в классе


class User(BaseModel):
    id: int
    role: str
    name: str
    degree: Optional[List[Degree]] = []  # не у всех юзеров, есть 'degree'


class Trade(BaseModel):
    id: int
    user_id: int
    currency: str = Field(max_length=5)  # [validation] максимум 5 символов
    side: str
    price: float = Field(ge=0)  # [validation] больше или равно 0
    amount: float


app = FastAPI(
    title="FX"
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/users/{user_id}", response_model=List[User])  # (валидация)
def get_user(user_id: int):
    return [user for user in fake_users if user.get("id") == user_id]


@app.post("/users/{user_id}")
def change_user_name(user_id: int, new_name: str):
    current_user = list(filter(lambda user: user.get("id") == user_id, fake_users))[0]
    current_user["name"] = new_name
    return {"status": 200, "data": current_user}


@app.post("/trades")
def add_trades(trades: List[Trade]):
    fake_trades.extend(trades)
    return {"status": 200, "data": fake_trades}


def common_parameters(
        q: Union[str, None] = None, skip: int = 0, limit: int = 100
):
    return {"q": q, "skip": skip, "limit": limit}


@app.get("/items/")
def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons


@app.get("/clients/")
def read_users(commons: Annotated[dict, Depends(common_parameters)]):
    return commons


