from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt
import datetime

app = FastAPI()

# Dummy database for empanadas and users
fake_db = {
    "empanadas": [
        {"id": 1, "name": "carne", "quantity": 10},
        {"id": 2, "name": "pollo", "quantity": 15},
        {"id": 3, "name": "vegetariana", "quantity": 5},
    ],
    "users": {
        "user": "pass"  # Hardcoded username and password
    }
}

SECRET_KEY = "mi_clave_secreta"
ALGORITHM = "HS256"

class Empanada(BaseModel):
    id: int
    name: str
    quantity: int

class CreateEmpanada(BaseModel):
    name: str
    quantity: int

class UpdateQuantity(BaseModel):
    quantity: int

class UpdateEmpanada(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None

class LoginRequest(BaseModel):
    username: str
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@app.post("/token")
async def login(login_request: LoginRequest):
    username = login_request.username
    password = login_request.password
    if fake_db["users"].get(username) == password:
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        token = jwt.encode({"sub": username, "exp": expiration}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@app.get("/empanadas", response_model=List[Empanada])
async def get_empanadas(name: Optional[str] = None, id: Optional[int] = None):
    if id is not None:
        result = [e for e in fake_db["empanadas"] if e["id"] == id]
    elif name:
        result = [e for e in fake_db["empanadas"] if e["name"] == name]
    else:
        result = fake_db["empanadas"]
    return result

@app.post("/empanadas", response_model=Empanada, status_code=status.HTTP_201_CREATED)
async def create_empanada(empanada: CreateEmpanada, token: str = Depends(oauth2_scheme)):
    verify_token(token)
    next_id = max(e["id"] for e in fake_db["empanadas"]) + 1 if fake_db["empanadas"] else 1
    new_empanada = {"id": next_id, **empanada.dict()}
    fake_db["empanadas"].append(new_empanada)
    return new_empanada

@app.put("/empanadas/{empanada_id}", response_model=Empanada)
async def update_empanada(empanada_id: int, update: UpdateEmpanada, token: str = Depends(oauth2_scheme)):
    verify_token(token)
    for i, e in enumerate(fake_db["empanadas"]):
        if e["id"] == empanada_id:
            if update.name is not None:
                e["name"] = update.name
            if update.quantity is not None:
                e["quantity"] = update.quantity
            fake_db["empanadas"][i] = e
            return e
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empanada not found")

@app.delete("/empanadas/{empanada_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_empanada(empanada_id: int, token: str = Depends(oauth2_scheme)):
    verify_token(token)
    global fake_db
    fake_db["empanadas"] = [e for e in fake_db["empanadas"] if e["id"] != empanada_id]
    return
