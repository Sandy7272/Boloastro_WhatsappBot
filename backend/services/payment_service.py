# backend/services/payment_service.py

def add_money(wallet_db, user, amount):

    if user not in wallet_db:
        wallet_db[user] = 0

    wallet_db[user] += amount
    return wallet_db[user]


def deduct_money(wallet_db, user, amount):

    if wallet_db.get(user, 0) < amount:
        return False

    wallet_db[user] -= amount
    return True
