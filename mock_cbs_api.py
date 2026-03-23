import random
from datetime import date, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import re as _re

app = FastAPI(title="Mock CBS API", version="1.0.0")

_ACCOUNTS = {
    "1234567890": {
        "account_number":    "1234567890",
        "account_holder":    "Ram Prasad Sharma",
        "account_type":      "Savings",
        "product_name":      "Sunaulo Bachat Khata",
        "currency":          "NPR",
        "balance":           125_430.50,
        "available_balance": 120_430.50,
        "status":            "Active",
        "branch":            "Kathmandu Main Branch",
        "ifsc":              "LSBL0001001",
        "opened_date":       "2019-03-15",
    },
    "9876543210": {
        "account_number":    "9876543210",
        "account_holder":    "Sita Devi Thapa",
        "account_type":      "Current",
        "product_name":      "Business Current Account",
        "currency":          "NPR",
        "balance":           4_892_000.00,
        "available_balance": 4_700_000.00,
        "status":            "Active",
        "branch":            "Pokhara Branch",
        "ifsc":              "LSBL0002001",
        "opened_date":       "2017-07-22",
    },
    "1122334455667": {
        "account_number":    "1122334455667",
        "account_holder":    "Bikash Kumar Rai",
        "account_type":      "Fixed Deposit",
        "product_name":      "Samman Bachat Khata",
        "currency":          "NPR",
        "balance":           500_000.00,
        "available_balance": 0.00,
        "status":            "Active",
        "branch":            "Biratnagar Branch",
        "ifsc":              "LSBL0003001",
        "opened_date":       "2022-01-10",
        "maturity_date":     "2025-01-10",
        "interest_rate":     10.5,
    },
    "007123456789": {
        "account_number":    "007123456789",
        "account_holder":    "Anita Gurung",
        "account_type":      "Savings",
        "product_name":      "Shakti Bachat Khata",
        "currency":          "NPR",
        "balance":           18_750.00,
        "available_balance": 18_750.00,
        "status":            "Dormant",
        "branch":            "Lalitpur Branch",
        "ifsc":              "LSBL0004001",
        "opened_date":       "2015-06-01",
    },
    "LSB0012345678": {
        "account_number":    "LSB0012345678",
        "account_holder":    "Prakash Bahadur Magar",
        "account_type":      "Savings",
        "product_name":      "NRN Savings",
        "currency":          "USD",
        "balance":           3_210.75,
        "available_balance": 3_210.75,
        "status":            "Active",
        "branch":            "New Road Branch",
        "ifsc":              "LSBL0005001",
        "opened_date":       "2021-11-30",
    },
    "NMB98765432": {
        "account_number":    "NMB98765432",
        "account_holder":    "Sunita Karmacharya",
        "account_type":      "Recurring Deposit",
        "product_name":      "Smart Kista Bachat",
        "currency":          "NPR",
        "balance":           240_000.00,
        "available_balance": 240_000.00,
        "status":            "Active",
        "branch":            "Bhaktapur Branch",
        "ifsc":              "LSBL0006001",
        "opened_date":       "2023-04-05",
    },
    "0101234567890": {
        "account_number":    "0101234567890",
        "account_holder":    "Dipak Shrestha",
        "account_type":      "Loan",
        "product_name":      "Home Loan",
        "currency":          "NPR",
        "balance":           -3_200_000.00,
        "available_balance": 0.00,
        "status":            "Active",
        "branch":            "Thamel Branch",
        "ifsc":              "LSBL0007001",
        "opened_date":       "2020-08-15",
        "loan_outstanding":  3_200_000.00,
        "next_emi_date":     "2026-04-07",
        "emi_amount":        28_500.00,
    },
}

_TX = [
    ("Dr","ATM Withdrawal"), ("Cr","NEFT Credit"), ("Dr","UPI Payment"),
    ("Cr","Salary Credit"),  ("Dr","Bill Payment - NEA"), ("Dr","POS Purchase"),
    ("Cr","Fund Transfer Received"), ("Dr","Foneloan EMI"),
    ("Cr","Interest Credit"), ("Dr","Insurance Premium"),
]

def _norm(raw):
    return _re.sub(r"[\s\-]", "", raw).upper()

def _lookup(raw):
    n = _norm(raw)
    for key, data in _ACCOUNTS.items():
        if _norm(key) == n:
            return data
    raise HTTPException(status_code=404, detail=f"Account '{raw}' not found.")

def _gen_tx(account_number, n=5):
    seed = sum(ord(c) for c in account_number)
    rng  = random.Random(seed)
    txs  = []
    today = date.today()
    for i in range(n):
        dr_cr, desc = rng.choice(_TX)
        amount = round(rng.uniform(500, 50_000), 2)
        txs.append({
            "date": str(today - timedelta(days=i * rng.randint(1,4))),
            "description": desc, "dr_cr": dr_cr,
            "amount": amount, "currency": "NPR",
        })
    return txs

class AccountResponse(BaseModel):
    success: bool
    account_number: str
    account_holder: str
    account_type: str
    product_name: str
    currency: str
    balance: float
    available_balance: float
    status: str
    branch: str
    ifsc: str
    opened_date: str
    extra: Optional[dict] = None

class Transaction(BaseModel):
    date: str
    description: str
    dr_cr: str
    amount: float
    currency: str

class MiniStatementResponse(BaseModel):
    success: bool
    account_number: str
    account_holder: str
    transactions: list[Transaction]

@app.get("/api/v1/account/{account_number}", response_model=AccountResponse)
def get_account(account_number: str):
    data  = _lookup(account_number)
    extra = {}
    if "maturity_date"    in data: extra["maturity_date"]    = data["maturity_date"]
    if "interest_rate"    in data: extra["interest_rate"]    = data["interest_rate"]
    if "loan_outstanding" in data:
        extra["loan_outstanding"] = data["loan_outstanding"]
        extra["next_emi_date"]    = data["next_emi_date"]
        extra["emi_amount"]       = data["emi_amount"]
    return AccountResponse(
        success=True,
        account_number=data["account_number"],
        account_holder=data["account_holder"],
        account_type=data["account_type"],
        product_name=data["product_name"],
        currency=data["currency"],
        balance=data["balance"],
        available_balance=data["available_balance"],
        status=data["status"],
        branch=data["branch"],
        ifsc=data["ifsc"],
        opened_date=data["opened_date"],
        extra=extra or None,
    )

@app.get("/api/v1/account/{account_number}/mini-statement", response_model=MiniStatementResponse)
def get_mini_statement(account_number: str, count: int = Query(default=5, ge=1, le=10)):
    data = _lookup(account_number)
    return MiniStatementResponse(
        success=True,
        account_number=data["account_number"],
        account_holder=data["account_holder"],
        transactions=[Transaction(**t) for t in _gen_tx(account_number, n=count)],
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "Mock CBS API"}

