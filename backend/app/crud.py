# crud.py
from sqlalchemy.orm import Session
from . import models, schemas 
from decimal import Decimal
from datetime import datetime

def create_user(db: Session, email: str, name: str, hashed_password: str):
    user = models.User(email=email, name=name, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email==email).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id==user_id).first()

def create_group(db: Session, name: str, owner_id: int):
    g = models.Group(name=name, owner_id=owner_id)
    db.add(g)
    db.commit()
    db.refresh(g)
    # add owner as member
    gm = models.GroupMember(group_id=g.id, user_id=owner_id)
    db.add(gm)
    db.commit()
    return g

def get_groups_for_user(db: Session, user_id: int):
    return db.query(models.Group).join(models.GroupMember, models.Group.id==models.GroupMember.group_id)\
        .filter(models.GroupMember.user_id==user_id).all()

def add_member(db: Session, group_id: int, user_id: int):
    exists = db.query(models.GroupMember).filter(models.GroupMember.group_id==group_id, models.GroupMember.user_id==user_id).first()
    if exists:
        return exists
    gm = models.GroupMember(group_id=group_id, user_id=user_id)
    db.add(gm)
    db.commit()
    db.refresh(gm)
    return gm

def create_expense(db: Session, group_id: int, payer_id: int, amount: Decimal, description: str, shares: list[schemas.Share]):
    exp = models.Expense(group_id=group_id, payer_id=payer_id, amount=amount, description=description, date=datetime.utcnow())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    
    # OLD logic for equal split is removed.
    # NEW: Iterate through the provided shares and save them directly.
    for s in shares:
        es = models.ExpenseShare(expense_id=exp.id, user_id=s.user_id, share=s.amount)
        db.add(es)
    db.commit()
    return exp

def list_expenses_for_group(db: Session, group_id: int):
    return db.query(models.Expense).filter(models.Expense.group_id==group_id).all()


# crud.py
# ... other functions ...

def delete_group_by_id(db: Session, group_id: int):
    # Find all expenses related to the group
    expenses_to_delete = db.query(models.Expense).filter(models.Expense.group_id == group_id).all()
    expense_ids = [e.id for e in expenses_to_delete]

    # 1. Delete all expense shares for those expenses
    if expense_ids:
        db.query(models.ExpenseShare).filter(models.ExpenseShare.expense_id.in_(expense_ids)).delete(synchronize_session=False)

    # 2. Delete all the expenses
    db.query(models.Expense).filter(models.Expense.id.in_(expense_ids)).delete(synchronize_session=False)

    # 3. Delete all group memberships
    db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).delete(synchronize_session=False)

    # 4. Delete the group itself
    db.query(models.Group).filter(models.Group.id == group_id).delete(synchronize_session=False)

    db.commit()




def compute_balances(db: Session, group_id: int):
    # returns dict user_id -> Decimal (positive: to receive, negative: owes)
    from collections import defaultdict
    balances = defaultdict(Decimal)
    exps = db.query(models.Expense).filter(models.Expense.group_id==group_id).all()
    for e in exps:
        shares = db.query(models.ExpenseShare).filter(models.ExpenseShare.expense_id==e.id).all()
        total_shares = Decimal("0.00")
        for s in shares:
            balances[s.user_id] -= Decimal(s.share)
            total_shares += Decimal(s.share)
        balances[e.payer_id] += total_shares
    # convert to regular dict
    return {k: float(v) for k,v in balances.items()}



# crud.py

# ... other functions ...

def get_members_of_group(db: Session, group_id: int):
    """Gets all users who are members of a specific group."""
    return db.query(models.User).join(models.GroupMember, models.User.id == models.GroupMember.user_id)\
        .filter(models.GroupMember.group_id == group_id).all()