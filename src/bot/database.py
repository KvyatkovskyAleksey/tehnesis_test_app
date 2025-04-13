import aiosqlite

DATABASE_URL = "bot_data.db"


async def init_db():
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price REAL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            xpath TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        )
        await db.commit()


async def save_product(
    title: str,
    url: str,
    xpath: str,
    price: float | None,
):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
        INSERT INTO products (price, title, url, xpath) 
        VALUES (?, ?, ?, ?)""",
            (price, title, url, xpath),
        )
        await db.commit()
