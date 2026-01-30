from config import Config


def create_order(phone):
    """
    Create Razorpay payment link (demo now)
    """
    amount = Config.PRICE

    # Later you will integrate Razorpay API
    # For now dummy link
    return f"https://rzp.io/l/demo-payment?amount={amount}"


def verify_payment(phone):
    """
    Dummy payment check (always true for now)
    Later -> Razorpay webhook
    """
    return True
