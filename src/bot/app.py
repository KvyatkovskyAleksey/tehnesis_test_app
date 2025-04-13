import asyncio
import io
import os
import re
import traceback
from collections import defaultdict
from logging import getLogger
import urllib.parse

import pandas as pd
from aiogram import Dispatcher, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, Document
from black.cache import NamedTuple
from dotenv import load_dotenv

from browser_manager import BrowserManager
from database import init_db, save_product
from exceptions import IncorrectColumnsFileException

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

SUPPORTED_EXEL_FILE_EXTENSIONS = ["xls", "xlsx", "xlsm", "xlsb", "odf", "ods", "odt"]
REQUIRED_COLUMNS = ["title", "url", "xpath"]

logger = getLogger("bot")


browser_manager = BrowserManager()


@dp.startup()
async def on_startup():
    await browser_manager.start()
    logger.info("Browser started successfully")


@dp.shutdown()
async def on_shutdown():
    await browser_manager.stop()
    logger.info("Browser stopped successfully")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        "Привет! 🤖\
        Пожалуйста загрузи файл (xlsx) с колонками: title | url | xpath"
    )


@dp.message(F.document)
async def excel_file_handler(message: Message):
    document: Document = message.document
    if not uploaded_file_type_is_correct(document):
        await message.answer(
            "🚫 Этот тип файла не поддерживается. Пожалуйста загрузите Excel файл или csv."
        )
        return
    try:
        await message.answer("Ваш файл обрабатывается...")
        df = await load_file_to_dataframe(document)
        check_uploaded_dataframe(df)
        prices_by_sites = defaultdict(list)
        for _, row in df.iterrows():
            site, price = await handle_dataframe_row(row, message)
            if site and price:
                prices_by_sites[site].append(price)
        await message.answer(f"Файл загружен. {df.shape[0]} строк загружено.")
        for site, values in prices_by_sites.items():
            if values:
                await message.answer(
                    f"Средняя цена на сайте: {site} - {sum(values) / len(values)}"
                )
            else:
                await message.answer(f"Не удалось собрать данные для сайта: {site}")
    except IncorrectColumnsFileException:
        logger.info("Incorrect columns file")
        await message.answer(f"Проверьте файл и правильность колонок в нём.")
    except Exception:
        import traceback

        logger.error(traceback.format_exc())
        await message.answer(f"Что-то пошло не так. Проверьте ваш файл.")


def get_file_extension(document: Document) -> str:
    return document.file_name.split(".")[-1]


async def load_file_to_dataframe(document: Document) -> pd.DataFrame:
    extension = get_file_extension(document)
    file_buffer = io.BytesIO()
    await document.bot.download(document.file_id, destination=file_buffer)
    if extension not in SUPPORTED_EXEL_FILE_EXTENSIONS:
        return pd.read_csv(file_buffer)
    elif extension == "csv":
        return pd.read_csv(file_buffer)
    else:
        raise ValueError("Unsupported file type")


def uploaded_file_type_is_correct(document: Document) -> bool:
    """Check if the uploaded file is an Excel or csv file."""
    extension = get_file_extension(document)
    return extension in SUPPORTED_EXEL_FILE_EXTENSIONS + ["csv"]


def check_uploaded_dataframe(df: pd.DataFrame) -> bool:
    """Check if the uploaded dataframe has the correct number of columns."""
    df_columns = df.columns.tolist()
    if any(column not in df_columns for column in REQUIRED_COLUMNS):
        raise IncorrectColumnsFileException(
            "Файл должен содержать следующие колонки: title | url | xpath."
        )
    return True


def get_price_from_string(price: str) -> float:
    """Convert a string price (integer or decimal) to a float."""
    match = re.search(r"(\d+\.\d+|\d+)", re.sub(r"\s+", "", price))
    if not match:
        raise ValueError(f"Invalid price format: {price}")
    return float(match.group())


RowOutput = NamedTuple(
    "row_output",
    [
        ("site", str),
        ("price", float | None),
    ],
)


async def handle_dataframe_row(row: pd.Series, message: Message) -> RowOutput:
    """Handle a single row of the uploaded dataframe."""
    domain = urllib.parse.urlparse(row["url"]).netloc
    if not domain:
        await message.answer(
            f"Не получилось извлечь цену для:\n {row['title']}\n{row['url']}\n{row['xpath']}"
        )
        return RowOutput(site=domain, price=None)
    try:
        price = await browser_manager.get_price(row["url"], row["xpath"])
        cleaned_price = get_price_from_string(price)
        await save_product(
            title=row["title"],
            url=row["url"],
            xpath=row["xpath"],
            price=cleaned_price,
        )
        await message.answer(
            f"Название: {row['title']}\n{row['url']}\n{row['xpath']}\nЦена: {cleaned_price}"
        )
        return RowOutput(site=domain, price=cleaned_price)
    except Exception:

        logger.error(
            f"Failed to send message for\n {row['title']}\n{traceback.format_exc()}"
        )

        await save_product(
            title=row["title"],
            url=row["url"],
            xpath=row["xpath"],
            price=None,
        )
        await message.answer(
            f"Не получилось извлечь цену для:\n {row['title']}\n{row['url']}\n{row['xpath']}"
        )
        return RowOutput(site=domain, price=None)


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
