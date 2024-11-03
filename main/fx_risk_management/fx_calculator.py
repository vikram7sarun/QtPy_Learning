

def calculate_position_size(account_balance, risk_percent, stop_loss_pips, pip_value):
    '\n    Calculate position size based on the risk percentage, account balance, stop loss, and pip value.\n    '
    risk_amount = ((risk_percent / 100) * account_balance)
    position_size = (risk_amount / (stop_loss_pips * pip_value))
    return position_size
