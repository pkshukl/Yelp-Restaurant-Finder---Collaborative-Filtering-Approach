import argparse
import logging
import sqlite3

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

from load_data.load import load_all_json_files

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

DATABASE = "recommender.db"

load_all_json_files(DATABASE)

app = Flask(__name__)
CORS(app)  # This allows the app to accept requests from any origin


def query_db(query, params=(), commit=False):
    logger.debug("Executing Query")
    logger.debug(query)
    logger.debug(params)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return rows


def _search_businesses(
    name=None,
    city=None,
    state=None,
    postal_code=None,
    categories=None,
    business_id=None,
    user_id=None,
    per_page=20,
    page=1,
    order_by=None,
):
    if per_page < 1 or per_page > 100:
        return {"error": "Per page must be between 1 and 100"}, 400

    query_conditions = []

    if name:
        query_conditions.append(("UPPER(name) LIKE UPPER(?)", f"%{name}%"))
    if city:
        query_conditions.append(("UPPER(city) = UPPER(?)", city))
    if state:
        query_conditions.append(("UPPER(state) = UPPER(?)", state))
    if postal_code:
        query_conditions.append(("postal_code = ?", postal_code))
    if categories:
        query_conditions.append(("UPPER(categories) LIKE UPPER(?)", f"%{categories}%"))
    if business_id:
        query_conditions.append(("business_id = ?", business_id))
    if not query_conditions:
        return {"error": "At least one search field is required"}, 400

    query_conditions_str = " AND ".join(
        [condition[0] for condition in query_conditions]
    )
    query_params = [condition[1] for condition in query_conditions]

    # Get column names from the business table
    column_names = [column[1] for column in query_db("PRAGMA table_info(business)")]
    # Validate the user-provided order_by fields
    if order_by:
        order_by_fields = order_by.split(",")
        for field in order_by_fields.copy():
            if field.split()[0].lower() not in column_names:
                return (
                    {
                        "error": f"Invalid order by field. Valid fields are {column_names}"
                    },
                    400,
                )
            if "business_id" in field:
                order_by_fields.remove(field)
        order_by_fields.append("business_id ASC")
        order_by = ", ".join(order_by_fields)
    else:
        order_by = "stars DESC, review_count DESC, business_id ASC"

    if recommendation_feature_flag and user_id and city:
        ratings_table_name = f"predicted_ratings_{city}_{user_id.replace('-','_')}"

        # Check if the table already exists
        check_table_exists_query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{ratings_table_name}'"
        table_exists = len(query_db(check_table_exists_query)) > 0

        # If the table does not exist, create it and populate it with the predicted ratings
        if not table_exists:
            logger.info(f"Creating table {ratings_table_name}")
            predicted_ratings = recommender.getTopRestaurants(user_id, city)

            query_create_ratings_table = f"""
            CREATE TABLE {ratings_table_name} (business_id TEXT PRIMARY KEY, rating REAL);
            """
            query_db(query_create_ratings_table, commit=True)

            query_insert_predicted_rating = f"""
                INSERT INTO {ratings_table_name} (business_id, rating) VALUES
                """
            for business_id, rating in predicted_ratings.items():
                query_insert_predicted_rating = (
                    query_insert_predicted_rating
                    + f"""('{business_id}', {rating}),\n"""
                )
            query_db(query_insert_predicted_rating[:-2] + ";", commit=True)

        query = f"""
        SELECT b.*, r.rating as predicted_rating
        FROM business b
        JOIN {ratings_table_name} r
        ON b.business_id = r.business_id
        WHERE {query_conditions_str}
        ORDER BY r.rating DESC, {order_by}
        LIMIT {per_page} OFFSET {(page-1) * per_page}
        """
    else:
        query = f"""
        SELECT * FROM business
        WHERE {query_conditions_str}
        ORDER BY {order_by}
        LIMIT {per_page} OFFSET {(page-1) * per_page}
        """
    rows = query_db(query, query_params)

    businesses = []
    for row in rows:
        attributes = {}
        for i in range(11, 60):
            column_name = row.keys()[i]
            if column_name.startswith("attributes_"):
                attribute_name = column_name[len("attributes_") :]
                if row[column_name]:
                    attributes[attribute_name] = row[column_name]

        hours = {}
        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            hours_column_name = f"hours_{day}"
            if row[hours_column_name] is not None:
                hours[day] = row[hours_column_name]

        categories = (
            row["categories"].split(", ") if row["categories"] is not None else []
        )

        business = {
            "business_id": row["business_id"],
            "name": row["name"],
            "address": row["address"],
            "city": row["city"],
            "state": row["state"],
            "postal_code": row["postal_code"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "stars": row["stars"],
            "review_count": row["review_count"],
            "is_open": row["is_open"],
            "attributes": attributes,
            "categories": categories,
            "hours": hours,
            "relevance_score": dict(row).get("predicted_rating", 0),
        }
        businesses.append(business)

    return {
        "businesses": businesses,
        "total_count": len(businesses),
        "page": page,
        "per_page": per_page,
    }, 200


@app.route("/businesses/search", methods=["GET"])
def search_businesses():
    name = request.args.get("name", "").strip()
    city = request.args.get("city", "").strip()
    state = request.args.get("state", "").strip()
    postal_code = request.args.get("postal_code", "").strip()
    categories = request.args.get("categories", "").strip()
    business_id = request.args.get("business_id", "").strip()
    user_id = request.args.get("user_id", "").strip()
    order_by = request.args.get("order_by", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    result, status_code = _search_businesses(
        name,
        city,
        state,
        postal_code,
        categories,
        business_id,
        user_id,
        per_page,
        page,
        order_by,
    )
    if type(result) == tuple:
        return result
    return jsonify(result), status_code


def _search_reviews(
    keyword=None,
    business_id=None,
    user_id=None,
    stars=None,
    date=None,
    attribute_name=None,
    attribute_value=None,
    page=1,
    per_page=20,
):
    if not keyword and not business_id and not user_id:
        return {"error": "Keyword or busines_id or user_id is required"}, 400
    if per_page < 1 or per_page > 100:
        return {"error": "Per page must be between 1 and 100"}, 400

    query_conditions = ["text LIKE ?"]
    query_params = [f"%{keyword}%"]

    if business_id:
        query_conditions.append("business_id = ?")
        query_params.append(business_id)
    if user_id:
        query_conditions.append("user_id = ?")
        query_params.append(user_id)
    if stars:
        query_conditions.append("stars >= ?")
        query_params.append(stars)
    if date:
        query_conditions.append("strftime('%Y-%m-%d', date) = ?")
        query_params.append(date)
    if attribute_name and attribute_value:
        query_conditions.append(
            f"business_id IN (SELECT business_id FROM business WHERE attributes_{attribute_name} = ?)"
        )
        query_params.append(attribute_value)

    query_conditions_str = " AND ".join(query_conditions)
    query = f"""
    SELECT * FROM review
    WHERE {query_conditions_str}
    ORDER BY date DESC, review_id ASC
    LIMIT ? OFFSET ?
    """
    query_params.append(per_page)
    query_params.append((page - 1) * per_page)
    rows = query_db(query, query_params)
    reviews = []
    for row in rows:
        review = {
            "review_id": row["review_id"],
            "user_id": row["user_id"],
            "business_id": row["business_id"],
            "stars": row["stars"],
            "date": row["date"],
            "text": row["text"],
            "useful": row["useful"],
            "funny": row["funny"],
            "cool": row["cool"],
        }
        reviews.append(review)

    filters = {
        "business_id": business_id,
        "user_id": user_id,
        "stars": stars,
        "date": date,
        attribute_name: attribute_value,
    }
    filters = {k: v for k, v in filters.items() if v}

    return {
        "reviews": reviews,
        "total_count": len(reviews),
        "filters": filters,
    }, 200


@app.route("/reviews/search", methods=["GET"])
def search_reviews():
    keyword = request.args.get("keyword", "").strip()
    business_id = request.args.get("business_id", "").strip()
    user_id = request.args.get("user_id", "").strip()
    stars = request.args.get("stars", "").strip()
    date = request.args.get("date", "").strip()
    attribute_name = request.args.get("attribute_name", "").strip()
    attribute_value = request.args.get("attribute_value", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    result, status_code = _search_reviews(
        keyword,
        business_id,
        user_id,
        stars,
        date,
        attribute_name,
        attribute_value,
        page,
        per_page,
    )
    return jsonify(result), status_code


@app.route("/businesses/<business_id>", methods=["GET"])
def get_business_by_id(business_id):
    business_data, status_code = _search_businesses(business_id=business_id, per_page=1)
    if business_data.get("error", ""):
        return jsonify(business), status_code
    elif business_data["total_count"] == 0:
        return jsonify({"error": "Business not found"}), 404
    elif business_data["total_count"] == 1:
        business = business_data["businesses"][0]
    else:
        return jsonify({"error": "unknown error"}), 500
    return jsonify(business), status_code


@app.route("/businesses/related/<business_id>")
def get_related_businesses(business_id):
    # Fetch the target business
    target_business, status_code = _search_businesses(
        business_id=business_id, per_page=1
    )
    if status_code != 200:
        return jsonify(target_business), status_code
    if target_business["total_count"] != 1:
        return jsonify({"error": "Business not found"}), 404

    target_business = target_business["businesses"][0]

    # Retrieve the categories and location of the target business
    categories = target_business["categories"]
    city = target_business["city"]
    state = target_business["state"]

    # Use the existing _search_businesses function to find related businesses
    related_businesses, status_code = _search_businesses(
        categories=categories, city=city, state=state
    )
    if status_code != 200:
        return jsonify(related_businesses), status_code

    # Remove the target business from the results
    related_businesses["businesses"] = [
        business
        for business in related_businesses["businesses"]
        if business["business_id"] != business_id
    ]

    # Return the related businesses
    return (
        jsonify({"related_restaurants": related_businesses["businesses"]}),
        status_code,
    )


@app.route("/businesses/<business_id>/photos", methods=["GET"])
def get_business_photos(business_id):
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    if per_page < 1 or per_page > 100:
        return jsonify({"error": "Per page must be between 1 and 100"}), 400

    # Query the database for photos related to the business_id
    query = f"""
    SELECT * FROM photo
    WHERE business_id = ?
    ORDER BY photo_id ASC
    LIMIT ? OFFSET ?
    """
    photos = query_db(query, (business_id, per_page, (page - 1) * per_page))

    # Check if there are any results
    if not photos:
        return jsonify({"error": "No photos found for this business"}), 404

    # Construct the response object
    response_photos = []
    for photo in photos:
        photo_data = {
            "photo_id": photo["photo_id"],
            "business_id": photo["business_id"],
            "caption": photo["caption"],
            "label": photo["label"],
            "url": f"/photos/{photo['photo_id']}.jpg",
        }
        response_photos.append(photo_data)

    return (
        jsonify(
            {
                "photos": response_photos,
                "total_count": len(response_photos),
                "page": page,
                "per_page": per_page,
            }
        ),
        200,
    )


@app.route("/photos/<path:photo_id>.jpg")
def serve_photo(photo_id):
    photo_directory = "./photos/photos"
    return send_from_directory(photo_directory, f"{photo_id}.jpg")


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-r",
        "--recommendation_feature_flag",
        action="store_true",
        default=False,
        help="recommendation feature flag",
    )

    args = parser.parse_args()
    recommendation_feature_flag = True

    if recommendation_feature_flag:
        from utils.recommender import Recommender

        recommender = Recommender()
    app.run(host="0.0.0.0", port=8080, debug=True)
else:
    recommendation_feature_flag = True
    if recommendation_feature_flag:
        from utils.recommender import Recommender

        recommender = Recommender()
