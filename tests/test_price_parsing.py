import pytest
from app import get_price_from_string


@pytest.mark.parametrize(
    "price_string, expected",
    [
        ("Цена: 12.99 рублей", 12.99),
        ("Стоимость товара: 1000.00 руб.", 1000.00),
        ("Итого 250.75 рублей", 250.75),
        ("Сумма: 999 руб.", 999.0),  # Целое число
        ("Цена всего лишь 79 руб", 79.0),  # Целое число
        ("Вы заплатили 0.99 рубля", 0.99),
        ("Товар стоит 475 рублей", 475.0),  # Целое число
        ("Со скидкой: 1500 руб", 1500.0),  # Целое число
        ("1 500 руб", 1500.0),  # Число с пробелом
    ],
)
def test_get_price_from_string(price_string, expected):
    assert get_price_from_string(price_string) == expected


@pytest.mark.parametrize(
    "invalid_string",
    [
        "Бесплатно",  # Нет цифр
        "",  # Пустая строка
        "Цена неизвестна",  # Нет данных по цене
        "Стоимость: десять рублей",  # Текстом вместо цифры
    ],
)
def test_get_price_from_string_invalid(invalid_string):
    with pytest.raises(ValueError):
        get_price_from_string(invalid_string)
