from app.tax import calculate_tax

def generate_invoice(amount):
    tax = calculate_tax(amount)
    return amount + tax