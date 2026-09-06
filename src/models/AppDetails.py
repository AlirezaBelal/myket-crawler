import sqlite3
from enum import Enum
from pathlib import Path
from typing import List, Optional


class Source(Enum):
    BAZAR = "bazar"
    MYKET = "myket"


class AppDetails:
    def __init__(
        self,
        name: str = "",
        package_name: str = "",
        author_name: str = "",
        author_phone_number: str = "",
        author_email: str = "",
        installation_count: int = 0,
        average_score: float = 0.0,
        comment_count: int = 0,
        star_1_count: int = 0,
        star_2_count: int = 0,
        star_3_count: int = 0,
        star_4_count: int = 0,
        star_5_count: int = 0,
        category: str = "",
        sub_category: str = "",
        last_update: int = 0,
        tags: Optional[List[str]] = None,
        price: int = 0,
        source: Source = Source.MYKET,
        short_description: str = "",
        long_description: str = "",
        homepage_url: str = "",
        version: str = "",
    ):
        self.name = name
        self.package_name = package_name
        self.author_name = author_name
        self.author_phone_number = author_phone_number
        self.author_email = author_email
        self.installation_count = installation_count
        self.average_score = average_score
        self.comment_count = comment_count
        self.star_1_count = star_1_count
        self.star_2_count = star_2_count
        self.star_3_count = star_3_count
        self.star_4_count = star_4_count
        self.star_5_count = star_5_count
        self.category = category
        self.sub_category = sub_category
        self.last_update = last_update
        self.tags = tags or []
        self.price = price
        self.source = source
        self.short_description = short_description
        self.long_description = long_description
        self.homepage_url = homepage_url
        self.version = version

    def save_to_db(self, db_name: str) -> None:
        db_path = Path(db_name)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_details (
                    name TEXT,
                    package_name TEXT,
                    author_name TEXT,
                    author_phone_number TEXT,
                    author_email TEXT,
                    homepage_url TEXT,
                    installation_count INTEGER,
                    average_score REAL,
                    comment_count INTEGER,
                    star_1_count INTEGER,
                    star_2_count INTEGER,
                    star_3_count INTEGER,
                    star_4_count INTEGER,
                    star_5_count INTEGER,
                    category TEXT,
                    sub_category TEXT,
                    last_update INTEGER,
                    tags TEXT,
                    price INTEGER,
                    source TEXT,
                    short_description TEXT,
                    long_description TEXT,
                    version TEXT,
                    PRIMARY KEY (package_name, source)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_installation_count "
                "ON app_details (installation_count)"
            )
            cursor.execute(
                """
                INSERT OR REPLACE INTO app_details (
                    name, package_name, author_name, author_phone_number, author_email,
                    homepage_url, installation_count, average_score, comment_count,
                    star_1_count, star_2_count, star_3_count, star_4_count, star_5_count,
                    category, sub_category, last_update, tags, price, source,
                    short_description, long_description, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.name,
                    self.package_name,
                    self.author_name,
                    self.author_phone_number,
                    self.author_email,
                    self.homepage_url,
                    self.installation_count,
                    self.average_score,
                    self.comment_count,
                    self.star_1_count,
                    self.star_2_count,
                    self.star_3_count,
                    self.star_4_count,
                    self.star_5_count,
                    self.category,
                    self.sub_category,
                    self.last_update,
                    ",".join(self.tags),
                    self.price,
                    self.source.value,
                    self.short_description,
                    self.long_description,
                    self.version,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
