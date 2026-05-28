import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from config import TOKEN
from extensions import APIException, CryptoConverter

def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    print("Бот запущен...")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            message_text = event.text.strip().lower()
            user_name = None
            try:
                # Получаем имя пользователя для приветствия
                user_info = vk.users.get(user_ids=user_id)
                user_name = user_info[0]['first_name']
            except:
                user_name = "Пользователь"

            try:
                if message_text in ["/start", "/help"]:
                    help_msg = (
                        f"Привет, {user_name}!\n\n"
                        "Инструкция по использованию:\n"
                        "Введите команду в формате:\n"
                        "<валюта1> <валюта2> <количество>\n\n"
                        "Пример: евро доллар 100\n\n"
                        "Доступные валюты: доллар, евро, рубль, биткоин, эфириум.\n"
                        "Для просмотра всех валют введите /values"
                    )
                    vk.messages.send(user_id=user_id, message=help_msg, random_id=0)

                elif message_text == "/values":
                    currencies = "Доступные валюты:\n• доллар (usd)\n• евро (eur)\n• рубль (rub)\n• биткоин (btc)\n• эфириум (eth)"
                    vk.messages.send(user_id=user_id, message=currencies, random_id=0)

                else:
                    # Разбираем сообщение на части
                    parts = message_text.split()
                    if len(parts) != 3:
                        raise APIException("Неверный формат команды. Пример: евро доллар 100")

                    base_name, quote_name, amount_str = parts

                    # Сопоставление русских названий с кодами
                    currency_map = {
                        "доллар": "usd", "доллар сша": "usd", "usd": "usd",
                        "евро": "eur", "eur": "eur",
                        "рубль": "rub", "руб": "rub", "rub": "rub",
                        "биткоин": "btc", "btc": "btc",
                        "эфириум": "eth", "eth": "eth"
                    }

                    base = currency_map.get(base_name)
                    quote = currency_map.get(quote_name)

                    if not base:
                        raise APIException(f"Неизвестная валюта: {base_name}")
                    if not quote:
                        raise APIException(f"Неизвестная валюта: {quote_name}")

                    # Получаем цену
                    total = CryptoConverter.get_price(base, quote, amount_str)

                    result_msg = f"Цена {amount_str} {base_name.upper()} в {quote_name.upper()} = {total}"
                    vk.messages.send(user_id=user_id, message=result_msg, random_id=0)

            except APIException as e:
                error_msg = f"Ошибка: {e}"
                vk.messages.send(user_id=user_id, message=error_msg, random_id=0)
            except Exception as e:
                error_msg = f"Неизвестная ошибка: {e}"
                vk.messages.send(user_id=user_id, message=error_msg, random_id=0)

if __name__ == "__main__":
    main()