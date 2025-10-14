# main.py
from fastapi import FastAPI, Depends, HTTPException
from . import models, db, crud, schemas, auth
from .db import engine
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List # Make sure this is imported
from decimal import Decimal

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


# main.py
# ... other endpoints ...

@app.delete("/groups/{group_id}")
def delete_group(group_id: int, current_user: models.User = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    group = db_session.query(models.Group).filter(models.Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Security check: Only the owner can delete the group
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this group")

    crud.delete_group_by_id(db_session, group_id=group_id)
    
    return {"status": "ok", "detail": "Group and all its expenses have been deleted."}

@app.post("/groups/{group_id}/settle")
def record_settlement(group_id: int, payload: schemas.SettlementCreate, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    # Security check: Ensure the person recording the payment is the one making the payment
    if current_user.id != payload.from_user_id:
        raise HTTPException(status_code=403, detail="You can only record payments made by yourself.")

    from_user = crud.get_user(db_session, payload.from_user_id)
    to_user = crud.get_user(db_session, payload.to_user_id)
    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="User not found.")

    description = f"Settlement: {from_user.name or from_user.email} paid {to_user.name or to_user.email}"
    

    settlement_share = schemas.Share(user_id=payload.to_user_id, amount=payload.amount)
    
    # The call to create_expense now uses the 'shares' keyword argument.
    exp = crud.create_expense(
        db=db_session,
        group_id=group_id,
        payer_id=payload.from_user_id,
        amount=payload.amount,
        description=description,
        shares=[settlement_share]  # Pass a list containing our single share object
    )
    # --- MODIFICATION END ---
    
    return {"status": "ok", "expense_id": exp.id}

# main.py

@app.get("/groups")
def my_groups(current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    groups_query = crud.get_groups_for_user(db_session, current_user.id)
    
    # Create a custom response to include owner's name
    result = []
    for group in groups_query:
        owner = crud.get_user(db_session, group.owner_id)
        result.append({
            "id": group.id,
            "name": group.name,
            "owner_id": group.owner_id,
            "owner_name": owner.name if owner else "Unknown"
        })
    return result

@app.post("/groups/{group_id}/expenses")
def add_expense(group_id: int, payload: schemas.ExpenseCreate, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    # --- ADD VALIDATION ---
    # Check if the sum of individual shares equals the total expense amount
    total_shares = sum(s.amount for s in payload.shares)
    if total_shares != payload.amount:
        raise HTTPException(
            status_code=400, 
            detail=f"The sum of shares ({total_shares}) does not match the total expense amount ({payload.amount})."
        )

    # Basic membership check (simplified)
    members_ids = [m.user_id for m in db_session.query(models.GroupMember).filter(models.GroupMember.group_id==group_id).all()]
    if payload.payer_id not in members_ids:
        raise HTTPException(status_code=400, detail="Payer must be a member of the group")
    for s in payload.shares:
        if s.user_id not in members_ids:
            raise HTTPException(status_code=400, detail=f"Participant with ID {s.user_id} is not a group member")
    
    # The function call is updated to pass the 'shares' payload
    exp = crud.create_expense(
        db_session, 
        group_id=group_id, 
        payer_id=payload.payer_id, 
        amount=payload.amount, 
        description=payload.description, 
        shares=payload.shares
    )
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

# main.py

# ... other endpoints ...

@app.post("/groups/{group_id}/members")
def add_group_member(group_id: int, payload: schemas.AddMemberRequest, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    """Adds a new member to a group."""
    group = db_session.query(models.Group).filter(models.Group.id == group_id).first()

    # Security check: Only the group owner can add new members
    if not group or group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group owner can add members")

    # Find the user to add
    user_to_add = crud.get_user_by_email(db_session, email=payload.email)
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User with that email not found")
    
    # Add the member using the existing CRUD function
    crud.add_member(db_session, group_id=group_id, user_id=user_to_add.id)
    
    return {"status": "ok", "detail": f"User {payload.email} added to the group."}

# ... rest of the endpoints ...

# main.py
# ... other imports ...

# ... other endpoints ...

@app.get("/groups/{group_id}/members", response_model=List[schemas.UserOut])
def get_group_members(group_id: int, current_user = Depends(auth.get_current_user), db_session: Session = Depends(auth.get_db)):
    """Endpoint to get all members of a group."""
    # Security check: ensure the current user is a member of the group they're querying
    member_ids = [m.user_id for m in db_session.query(models.GroupMember).filter(models.GroupMember.group_id==group_id).all()]
    if current_user.id not in member_ids:
        raise HTTPException(status_code=403, detail="Not a group member")
    
    members = crud.get_members_of_group(db_session, group_id)
    return members




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
