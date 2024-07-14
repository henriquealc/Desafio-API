'''Instalar as dependências necessárias - pip install fastapi sqlalchemy psycopg2-binary pydantic fastapi-pagination[sqlalchemy] '''

from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel
from fastapi_pagination import Page, pagination_params
from fastapi_pagination.ext.sqlalchemy import paginate

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Model
class AtletaModel(Base):
    __tablename__ = "atletas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    centro_treinamento = Column(String)
    categoria = Column(String)

# Pydantic model for response customization
class Atleta(BaseModel):
    nome: str
    centro_treinamento: str
    categoria: str

# FastAPI app instance
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Custom exception handler for IntegrityError
@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request, exc):
    # Assuming PostgreSQL specific error handling for uniqueness constraint violation
    return HTTPException(
        status_code=status.HTTP_303_SEE_OTHER,
        detail=f"Já existe um atleta cadastrado com o CPF: {exc.params['cpf']}",
    )

# Endpoint to add an athlete
@app.post("/atleta", response_model=Atleta)
async def create_atleta(atleta: Atleta):
    db = SessionLocal()
    try:
        db_atleta = AtletaModel(
            nome=atleta.nome,
            cpf=atleta.cpf,
            centro_treinamento=atleta.centro_treinamento,
            categoria=atleta.categoria
        )
        db.add(db_atleta)
        db.commit()
        db.refresh(db_atleta)
        return db_atleta
    except IntegrityError as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Endpoint to retrieve athletes with query parameters and response customization
@app.get("/atleta", response_model=Page[Atleta])
async def get_atletas(
    db: Session = Depends(get_db),
    nome: str = None,
    cpf: str = None,
    limit: int = pagination_params.limit,
    offset: int = pagination_params.offset
):
    query = db.query(AtletaModel)
    if nome:
        query = query.filter(AtletaModel.nome == nome)
    if cpf:
        query = query.filter(AtletaModel.cpf == cpf)
    
    return paginate(query)

# Create tables
Base.metadata.create_all(bind=engine)
