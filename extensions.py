import json
import requests

class APIException(Exception):
    """Собственное исключение для ошибок API"""
    pass

class CryptoConverter:
    @staticmethod
    def get_price(base: str, quote: str, amount: float) -> float:
        """
        Возвращает цену amount единиц базовой валюты в валюте котировки.
        Используется API cryptocompare.com (бесплатный, без ключа).
        """
        # Приводим к нижнему регистру для удобства
        base = base.lower().strip()
        quote = quote.lower().strip()

        # Список поддерживаемых валют (можно расширить)
        supported_currencies = ['usd', 'eur', 'rub', 'btc', 'eth']

        if base == quote:
            raise APIException(f"Невозможно перевести одинаковые валюты: {base}")

        if base not in supported_currencies:
            raise APIException(f"Валюта {base} не поддерживается. Доступные: {', '.join(supported_currencies)}")

        if quote not in supported_currencies:
            raise APIException(f"Валюта {quote} не поддерживается. Доступные: {', '.join(supported_currencies)}")

        try:
            amount = float(amount)
            if amount <= 0:
                raise APIException("Количество должно быть положительным числом")
        except ValueError:
            raise APIException(f"Неверный формат количества: '{amount}'. Ожидается число")

        # Формируем URL для API cryptocompare
        # Пример: https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD
        # Для фиатных валют тоже работает
        url = f"https://min-api.cryptocompare.com/data/price?fsym={base.upper()}&tsyms={quote.upper()}"

        try:
            response = requests.get(url, timeout=10)
            data = json.loads(response.text)
        except Exception as e:
            raise APIException(f"Ошибка при запросе к API: {e}")

        if quote.upper() not in data:
            raise APIException(f"Не удалось получить курс {base} -> {quote}. Проверьте правильность валют.")

        price = data[quote.upper()]
        total = price * amount
        return round(total, 2)