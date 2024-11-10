# fx_risk_management_backend.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class PositionSizeRequest(BaseModel):
    account_balance: float
    risk_percent: float
    stop_loss_pips: float
    pip_value: float

@app.post("/calculate_position_size")
def calculate_position_size(request: PositionSizeRequest):
    try:
        position_size = (request.account_balance * request.risk_percent / 100) / (request.stop_loss_pips * request.pip_value)
        return {"position_size": round(position_size, 2)}
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Stop loss and pip value cannot be zero.")
