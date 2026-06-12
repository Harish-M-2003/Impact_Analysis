from app.tax import calculate_tax

def test_tax():
    assert calculate_tax(100) == 18