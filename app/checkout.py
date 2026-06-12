from app.invoice import generate_invoice

def checkout(amount):
    return generate_invoice(amount)