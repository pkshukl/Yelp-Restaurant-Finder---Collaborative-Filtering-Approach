import csv
import json
import logging
import sqlite3

import pytest

from app import app

logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"home.html" in response.data


def test_search_businesses_no_keywords(client):
    response = client.get("/businesses/search")
    assert response.status_code == 400
    assert json.loads(response.data) == {
        "error": "At least one search field is required"
    }


def test_search_businesses_success(client):
    response = client.get(
        "/businesses/search",
        query_string={"name": "coffee", "city:": "Nashville", "per_page": 10},
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "businesses" in data
    assert "total_count" in data
    assert "page" in data
    assert "per_page" in data
    assert data["page"] == 1
    assert data["per_page"] == 10


def test_search_businesses_user_id(client):
    response = client.get(
        "/businesses/search",
        query_string={
            "user_id": "SD2wTe9oVhG4j2fAwo1yhg",
            "city": "Tampa",
            "per_page": 10,
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "businesses" in data
    assert len(data["businesses"]) == 10
    assert "total_count" in data
    assert "page" in data
    assert "per_page" in data
    assert data["page"] == 1
    assert data["per_page"] == 10


def test_search_businesses_many_user_ids(client):
    conn = sqlite3.connect("recommender.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT user_id FROM (SELECT user_id FROM user ORDER BY RANDOM() LIMIT 1000) a;"
    )
    rows = cur.fetchall()
    user_ids = []
    for row in rows:
        city_query = f"""
            SELECT b.city, COUNT(*) AS count
            FROM review AS r
            JOIN business AS b ON r.business_id = b.business_id
            JOIN user AS u ON r.user_id = u.user_id
            WHERE u.user_id = '{row["user_id"]}'
            GROUP BY b.city
            ORDER BY count DESC
            LIMIT 1;
        """
        cur.execute(city_query)
        result = cur.fetchone()
        user_ids.append((row["user_id"], result["city"]))
    conn.close()

    user_ids = sorted(user_ids, key=lambda x: x[1])
    counter = 0
    verified_users = []
    for user_id, city in user_ids:
        if city.lower() in (
            "tampa",
            "tucson",
            "philadelphia",
            "nashville",
            "indianapolis",
        ):
            response = client.get(
                "/businesses/search",
                query_string={
                    "user_id": user_id,
                    "city": city,
                    "per_page": 10,
                },
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "businesses" in data
            assert data["businesses"][0]["relevance_score"]
            assert data["businesses"][0]["name"]
            assert len(data["businesses"]) == 10
            assert "total_count" in data
            assert "page" in data
            assert "per_page" in data
            assert data["page"] == 1
            assert data["per_page"] == 10
            verified_users.append((user_id, city))
            counter += 1

    logger.info(f"Number of users tested: {counter}")
    with open("verified_users.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(verified_users)


def test_search_businesses_performance(client):
    for i in range(1, 101):
        response = client.get(
            "/businesses/search",
            query_string={
                "name": "coffee",
                "city": "Nashville",
                "page": i,
                "per_page": 100,
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["page"] == i


def test_search_reviews_no_keyword(client):
    response = client.get("/reviews/search")
    assert response.status_code == 400
    assert json.loads(response.data) == {
        "error": "Keyword or busines_id or user_id is required"
    }


def test_search_reviews_success(client):
    response = client.get(
        "/reviews/search",
        query_string={"keyword": "good"},
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "reviews" in data
    assert "total_count" in data
    assert "filters" in data
    assert data["filters"] == {}


SEARCH_REVIEWS_FILTER_PARAMS = [
    (
        {
            "keyword": "good",
            "business_id": "XQfwVwDr-v0ZS3_CbbE5Xw",
            "stars": "4",
            "attribute_name": "DogsAllowed",
            "attribute_value": "False",
        },
        {
            "business_id": "XQfwVwDr-v0ZS3_CbbE5Xw",
            "stars": "4",
            "DogsAllowed": "False",
        },
    ),
    (
        {"business_id": "XQfwVwDr-v0ZS3_CbbE5Xw", "date": "2018-07-07"},
        {"business_id": "XQfwVwDr-v0ZS3_CbbE5Xw", "date": "2018-07-07"},
    ),
    (
        {
            "keyword": "great",
            "business_id": "B5XSoSG3SfvQGtKEGQ1tSQ",
            "stars": "5",
        },
        {
            "business_id": "B5XSoSG3SfvQGtKEGQ1tSQ",
            "stars": "5",
        },
    ),
    (
        {
            "keyword": "amazing",
            "user_id": "yfFzsLmaWF2d4Sr0UNbBgg",
        },
        {
            "user_id": "yfFzsLmaWF2d4Sr0UNbBgg",
        },
    ),
]


@pytest.mark.parametrize("filters, expected_filters", SEARCH_REVIEWS_FILTER_PARAMS)
def test_search_reviews_filters(client, filters, expected_filters):
    response = client.get("/reviews/search", query_string=filters)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "reviews" in data
    assert data["total_count"] > 0
    assert "filters" in data
    assert data["filters"] == expected_filters


def test_get_business_by_id(client):
    # Replace 'some_business_id' with a valid business_id from your database
    business_id = "oaboaRBUgGjbo2kfUIKDLQ"
    response = client.get(f"/businesses/{business_id}")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "business_id" in data
    assert data["business_id"] == business_id

    # Test with a non-existent business_id
    response = client.get("/businesses/non_existent_business_id")
    assert response.status_code == 404


def test_get_related_businesses(client):
    # Replace 'some_business_id' with a valid business_id from your database
    business_id = "oaboaRBUgGjbo2kfUIKDLQ"
    response = client.get(f"/businesses/related/{business_id}")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "related_restaurants" in data

    # Check that the target business is not in the related_restaurants list
    for business in data["related_restaurants"]:
        assert business["business_id"] != business_id

    # Test with a non-existent business_id
    response = client.get("/businesses/related/non_existent_business_id")
    assert response.status_code == 404


def test_search_businesses_order_by(client):
    # Test ordering by stars ASC
    response = client.get(
        "/businesses/search",
        query_string={
            "name": "coffee",
            "order_by": "stars ASC",
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    prev_star = -1
    for business in data["businesses"]:
        assert prev_star <= business["stars"]
        prev_star = business["stars"]

    # Test ordering by review_count DESC and business_id ASC
    response = client.get(
        "/businesses/search",
        query_string={
            "name": "coffee",
            "order_by": "review_count DESC",
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    prev_review_count = float("inf")
    prev_business_id = ""
    for business in data["businesses"]:
        assert prev_review_count >= business["review_count"]
        if prev_review_count == business["review_count"]:
            assert prev_business_id < business["business_id"]
        prev_review_count = business["review_count"]
        prev_business_id = business["business_id"]

    # Test invalid order_by field
    response = client.get(
        "/businesses/search",
        query_string={
            "name": "coffee",
            "order_by": "invalid_field",
        },
    )
    assert response.status_code == 400


def test_search_businesses_filters(client):
    response = client.get(
        "/businesses/search",
        query_string={
            "name": "coffee",
            "city": "Tampa",
            "state": "FL",
            "categories": "cafe",
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "businesses" in data
    assert data["total_count"] > 0
