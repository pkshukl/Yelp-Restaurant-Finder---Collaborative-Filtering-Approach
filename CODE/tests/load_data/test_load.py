import pytest

from load_data.load import load_json_to_sqlite


def test_load_json_to_sqlite():
    file = "./yelp_data/yelp_academic_dataset_business.json"
    db_file = "recommender_test.db"
    tablename = "business"
    load_json_to_sqlite(file, db_file, tablename, if_exists="replace")
