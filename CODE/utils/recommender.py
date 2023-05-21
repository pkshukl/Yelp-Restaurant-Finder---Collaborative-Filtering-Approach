import logging
import pickle
import sqlite3

import pandas as pd


class Recommender:
    def __init__(self):
        self.algo = None
        self.current_location = None
        self.sentiments = pickle.load(open("./utils/pkl_files/sentiments.pkl", "rb"))

    def load_algo(self, location):
        try:
            if self.algo:
                del self.algo
            self.algo = pickle.load(
                open(
                    f"./utils/pkl_files/trained_model_{location.capitalize()}.pkl", "rb"
                )
            )
            self.current_location = location
        except Exception as e:
            logging.error(
                f"Pickle load failed for {location} - check that algo_xx and sentiments pkl files are present"
            )
            raise

    def getTopRestaurants(self, userId: str, location: str) -> dict:
        res = {}
        location = location.lower()

        if location not in [
            "nashville",
            "philadelphia",
            "tampa",
            "tucson",
            "indianapolis",
        ]:
            return res

        if location != self.current_location:
            self.load_algo(location)

        try:
            with sqlite3.connect("recommender.db") as conn:
                query = f"SELECT business_id FROM business_for_algos WHERE city = '{location}'"
                df_restaurants = pd.read_sql_query(query, conn)["business_id"]
        except Exception as e:
            logging.error("Error querying the SQLite3 database")
            raise

        for i in range(len(df_restaurants)):
            pred = self.algo.predict(uid=userId, iid=df_restaurants[i])
            # pred has a weight of 70%
            rating = 0
            if pred is not None:
                rating = pred.est * 2 * 0.7

            converted_score = 0
            snt = self.sentiments[df_restaurants[i]]
            if snt is not None or len(snt) > 0:
                converted_score = snt["polarity"] * 10 * 0.3

            res[pred.iid] = rating + converted_score

        if len(res) > 0:
            sorted_res = dict(sorted(res.items(), key=lambda x: x[1], reverse=True))
            return sorted_res
        else:
            return res


# This is how you would call it
# r = Recommender()
# print(r.getTopRestaurants("a732", "tucson"))
# print(r.getTopRestaurants("AaJ9d4OrFmgc4S_U2QiSZg", "tampa"))
# print(r.getTopRestaurants("fl4Iacyefm1t4Z0BaxocNQ", "indianapolis"))
