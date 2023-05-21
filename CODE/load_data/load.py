import json
import logging
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)


def load_json_to_sqlite(
    file: str,
    db_file: str,
    tablename: str,
    if_exists: str = "fail",
    chunksize: int = 100000,
) -> None:
    logger.debug(f"Loading table: {tablename}")

    def flatten_json(json_data: dict) -> dict:
        out = {}
        for key, value in json_data.items():
            if isinstance(value, dict):
                flat = flatten_json(value)
                for sub_key, sub_value in flat.items():
                    out[f"{key}_{sub_key}"] = sub_value
            else:
                out[key] = value
        return out

    def process_chunk(chunk: list[dict]) -> pd.DataFrame:
        flattened_data = [flatten_json(record) for record in chunk]
        return pd.DataFrame(flattened_data)

    with open(file, "r") as f, sqlite3.connect(db_file) as conn:
        if if_exists == "skip_or_fail":
            if_exists = "fail"
            table_exists = conn.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tablename}';"
            ).fetchone()
            if table_exists:
                logger.info(
                    f"Table {tablename} already exists so loading data is being skipped."
                )
                return

        chunk = []
        for i, line in enumerate(f):
            json_data = json.loads(line.strip())
            if json_data:
                chunk.append(json_data)

            if len(chunk) == chunksize:
                df_chunk = process_chunk(chunk)
                df_chunk.to_sql(tablename, conn, if_exists=if_exists, index=False)
                if_exists = (
                    "append"  # For subsequent chunks, append to the existing table
                )
                chunk = []  # Reset the chunk
                logger.debug(f"Processed chunk {(i+1) / chunksize}")

        if chunk:
            df_chunk = process_chunk(chunk)
            df_chunk.to_sql(tablename, conn, if_exists=if_exists, index=False)


def load_all_json_files(db_file):
    files = [
        "./yelp_data/yelp_academic_dataset_business.json",
        "./yelp_data/yelp_academic_dataset_checkin.json",
        "./yelp_data/yelp_academic_dataset_review.json",
        "./yelp_data/yelp_academic_dataset_tip.json",
        "./yelp_data/yelp_academic_dataset_user.json",
        "./photos/photos.json",
    ]
    for file in files:
        if file == "./photos/photos.json":
            tablename = "photo"
        else:
            tablename = file.split(".")[1].split("_")[-1]
        load_json_to_sqlite(file, db_file, tablename, if_exists="skip_or_fail")
        create_indexes(db_file, tablename)
    # NOTE: Cannot get FTS to work
    # create_fts5_review_table(db_file)
    load_prediction_csv_files_to_sqlite(db_file, "./yelp_data/")


def create_indexes(db_file: str, tablename: str) -> None:
    with sqlite3.connect(db_file) as conn:
        index_check_sql = f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{tablename}' AND name=?;"
        columns_sql = f"PRAGMA table_info('{tablename}');"
        columns = conn.execute(columns_sql).fetchall()

        for column in columns:
            column_name = column[1]
            if column_name.endswith("_id"):
                index_name = f"{tablename}_{column_name}_idx"
                index_exists = conn.execute(index_check_sql, (index_name,)).fetchone()

                if not index_exists:
                    index_sql = (
                        f"CREATE INDEX {index_name} ON {tablename}({column_name});"
                    )
                    conn.execute(index_sql)
                    logger.debug(f"Index {index_name} created for table {tablename}")


def create_fts5_review_table(db_file: str) -> None:
    with sqlite3.connect(db_file) as conn:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='review_fts';"
        ).fetchone()

        if not table_exists:
            conn.execute(
                "CREATE VIRTUAL TABLE review_fts USING fts5(review_id, text, content='review', content_rowid='review_id');"
            )
            conn.execute(
                "INSERT INTO review_fts(review_id, text) SELECT review_id, text FROM review;"
            )
            logger.debug("Created FTS5 virtual table for the review table")
        else:
            logger.debug("FTS5 virtual table for the review table already exists")


import glob
import os


def load_prediction_csv_files_to_sqlite(db_file: str, csv_directory: str) -> None:
    csv_files = glob.glob(os.path.join(csv_directory, "*.csv"))
    tablename = "business_for_algos"

    with sqlite3.connect(db_file) as conn:
        table_exists = conn.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tablename}';"
        ).fetchone()
        if table_exists:
            table_count = conn.execute(f"SELECT COUNT(*) FROM {tablename};").fetchone()
            if table_count[0] > 0:
                logger.info(
                    f"Table {tablename} already exists so loading data is being skipped."
                )
                return

        conn.execute(
            f"""
        CREATE TABLE IF NOT EXISTS {tablename} (
            business_id TEXT,
            city TEXT
        );
        """
        )

        for csv_file in csv_files:
            city = os.path.basename(csv_file).split("_")[-1].split(".")[0]
            df = pd.read_csv(csv_file)
            df = df[["business_id"]].copy()
            df.drop_duplicates(subset="business_id", inplace=True)
            df["city"] = city.lower()
            df.to_sql(tablename, conn, if_exists="append", index=False)
        logger.info(f"Table {tablename} has been populated.")
