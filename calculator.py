def calculate_collateral(prices):
    if not prices:
        return {
            "average_price": 0,
            "collateral_value": 0,
            "cars_parsed": 0
        }

    average_price = sum(prices) / len(prices)
    collateral_value = average_price * 0.8
    return {
        "average_price": round(average_price),  # Целые числа для рублей
        "collateral_value": round(collateral_value),
        "cars_parsed": len(prices)
    }