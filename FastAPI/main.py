from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine
import models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(CORSMiddleware, allow_origins=origins)  # CORS 미들웨어 적용


# pydantic 모델 선언. Front-end로 부터 받은 request의 validation을 담당
class TransactionBase(BaseModel):
    amount: float
    category: str
    description: str
    is_income: bool
    date: str


class TransationModel(TransactionBase):
    id: int

    class Config:
        orm_mode = True


def get_db():
    # dependency injection for application to try database connection
    # when we don't need the db session anymore, it will be returned to connection pool automatically
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)  # fastAPI가 DB 메타데이터를 이용하여 테이블을 자동생성하도록 설정


@app.post("/transactions/", response_model=TransationModel)
async def create_transaction(transaction: TransactionBase, db: db_dependency):
    db_transaction = models.Transaction(
        **transaction.dict()
    )  # 파라미터로 전달받은 transaction의 모든 값을 models.Transaction 테이블의 값으로 변환
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)  # 저장된 결과를 돌려받아서 db_transaction에 저장. id값이 포함되게됨
    return db_transaction


@app.get("/transactions", response_model=List[TransationModel])
async def read_transactions(db: db_dependency, skip: int = 0, limit: int = 100):
    transactions = db.query(models.Transaction).offset(skip).limit(limit).all()
    return transactions
