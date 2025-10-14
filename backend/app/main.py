# main.py
from fastapi import FastAPI, Depends, HTTPException
from . import models, db, crud, schemas, auth
from .db import engine
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Splitter Service")

@app.post("/auth/register", response_model=schemas.UserOut)
def register(u: schemas.UserCreate, db_session: Session = Depends(auth.get_db)):
    existing = crud.get_user_by_email(db_session, u.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = auth.get_password_hash(u.password)
    user = crud.create_user(db_session, email=u.email, name=u.name or "", hashed_password=hashed)
    return user

@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db_session: Session = Depends(auth.get_db)):
    user = crud.get_user_by_email(db_session, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = auth.create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserOut)
def read_me(current_user = Depends(auth.get_current_user)):
    return current_user

@app.post("/groups", response_model=schemas.GroupOut)
def create_group(g: schemas.GroupCreate, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    group = crud.create_group(db_session, name=g.name, owner_id=current_user.id)
    return group

@app.get("/groups")
def my_groups(current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    groups = crud.get_groups_for_user(db_session, current_user.id)
    return groups

@app.post("/groups/{group_id}/expenses")
def add_expense(group_id: int, payload: schemas.ExpenseCreate, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    # basic membership check (simplified)
    members = [m.user_id for m in db_session.query(models.GroupMember).filter(models.GroupMember.group_id==group_id).all()]
    if payload.payer_id not in members:
        raise HTTPException(status_code=400, detail="Payer must be a member of the group")
    for u in payload.participants:
        if u not in members:
            raise HTTPException(status_code=400, detail="All participants must be group members")
    exp = crud.create_expense(db_session, group_id=group_id, payer_id=payload.payer_id, amount=payload.amount, description=payload.description, participants=payload.participants)
    return {"status":"ok", "expense_id": exp.id}

@app.get("/groups/{group_id}/balances")
def group_balances(group_id: int, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    # membership check (simplified)
    members = [m.user_id for m in db_session.query(models.GroupMember).filter(models.GroupMember.group_id==group_id).all()]
    if current_user.id not in members:
        raise HTTPException(status_code=403, detail="Not a group member")
    balances = crud.compute_balances(db_session, group_id)
    # attach user info
    result = []
    for uid, bal in balances.items():
        user = crud.get_user(db_session, uid)
        result.append({"user_id": uid, "email": user.email if user else None, "name": user.name if user else None, "balance": round(bal,2)})
    return result

@app.get("/groups/{group_id}/settlement")
def settlement_plan(group_id: int, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    balances = crud.compute_balances(db_session, group_id)
    # simple greedy settlement
    creditors = []
    debtors = []
    for uid, bal in balances.items():
        if bal > 0:
            creditors.append([bal, uid])
        elif bal < 0:
            debtors.append([-bal, uid])
    creditors.sort(reverse=True)
    debtors.sort(reverse=True)
    i = j = 0
    plan = []
    while i < len(debtors) and j < len(creditors):
        owe_amt, debtor = debtors[i]
        recv_amt, creditor = creditors[j]
        transfer = min(owe_amt, recv_amt)
        plan.append({"from": debtor, "to": creditor, "amount": round(transfer,2)})
        owe_amt -= transfer
        recv_amt -= transfer
        if owe_amt == 0:
            i += 1
        else:
            debtors[i][0] = owe_amt
        if recv_amt == 0:
            j += 1
        else:
            creditors[j][0] = recv_amt
    return plan
