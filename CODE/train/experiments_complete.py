import pandas as pd
import os, time, pickle, argparse
import sentiment
from surprise import Dataset, Reader, KNNBasic, NormalPredictor, KNNWithZScore, accuracy, KNNBaseline, KNNWithMeans, SlopeOne
from surprise.model_selection import cross_validate, train_test_split, GridSearchCV

#business_json_path = "data/yelp_business.json"
#reviews_json_path = "data/yelp_review.json"

business_json_path = "./yelp_data/yelp_academic_dataset_business.json"
reviews_json_path = "./yelp_data/yelp_academic_dataset_review.json"

class Experiments():

    def __init__(self):
        self.df_rest = None
        self.df_reviews = None
        self.df_full = None
        self.df_city_reviews = None
        self.cities = ['Philadelphia', 'Nashville', 'Tampa', 'Indianapolis', 'Tucson']

    def are_data_files_present(self):
        for city in self.cities:
            filename1 = 'trained_model_' + city + '.pkl'
            if not os.path.isfile(filename1):
                return False
            filename2 = 'df_' + city + '.csv'
            if not os.path.isfile(filename2):
                return False
        if not os.path.isfile('sentiments.pkl'):
            return False
        if not os.path.isfile('dataframe_reviews.pkl'):
            return False

        return True


    def load_data(self):
        # read business json
        df_b = pd.read_json(business_json_path, lines=True)
        # filter and reduce size of dataframe
        df_b = df_b[df_b["is_open"] == 1]
        drop_columns = ["hours", "is_open"]
        df_b = df_b.drop(drop_columns, axis=1)
        # filter results to restaurants and bars
        df_rest = df_b[df_b["categories"].str.contains("Restaurants|Bars", case=False, na=False)]
        # filter results to businesses with > 500 reviews
        self.df_rest = df_rest[df_rest["review_count"] > 500]
        print("# of restaurants fitting criteria: " + str(len(self.df_rest)))

        # read review json - in chunks of 100,000 lines
        df_reviews_iter = pd.read_json(reviews_json_path, lines=True, chunksize=100000)
        df_reviews = pd.DataFrame()
        # filter results to reviews for businesses in the df_rest df
        for df in df_reviews_iter:
            df = df[df['business_id'].isin(df_rest['business_id'])]
            df_reviews = pd.concat([df_reviews, df])
        self.df_reviews = df_reviews
        print("# of reviews of restaurants|bars: " + str(len(self.df_reviews)))

        # Merge the two dataframes on business_id
        df_full_list = pd.merge(df_rest, df_reviews, on='business_id', how='inner')
        # Drop unneeded columns
        drop_columns2 = ['name', 'address', 'latitude', 'longitude', 'attributes', 'categories']
        df_full_list = df_full_list.drop(drop_columns2, axis=1)
        self.df_full = df_full_list
        print("Size of full df: " + str(len(self.df_full)))

        # Write to pickle file
        pickle.dump(df_full_list, open("dataframe_reviews.pkl", 'wb'))

    def load_pkl_reviews(self):
        if os.path.isfile("dataframe_reviews.pkl"):
            self.df_full = pickle.load(open("dataframe_reviews.pkl", 'rb'))

    def load_pkl_models(self, city):
        if os.path.isfile("trained_model_" + city + ".pkl"):
            return pickle.load(open("trained_model_" + city + ".pkl", 'rb'))

    def create_city_data(self, sample_size=70000):
        dfs = {}
        for i in range(len(self.cities)):
            dfs[self.cities[i]] = \
                self.df_full.loc[self.df_full['city'] == self.cities[i]].sample(n=sample_size)
            dfs[self.cities[i]].to_csv("df_" + self.cities[i] + ".csv")
        self.df_city_reviews = dfs

    def build_sentiment_scores(self):
        sentiments = sentiment.Score_All_Restaurants(self.df_full)
        pickle.dump(sentiments, open("sentiments.pkl", 'wb'))

    def find_best_params(self):
        df_exp = self.df_full.head(n=60000)

        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(df_exp[['user_id', 'business_id', 'stars_y']], reader)

        param_grid = {
            'bsl_options': {
                'method': ['als', 'sgd'],
            },
            'k': [2, 3],
            'sim_options': {
                'name': ['pearson_baseline'],
                'min_support': [1, 5],
                'user_based': [True],
            },
        }
        gs = GridSearchCV(KNNBaseline, param_grid, measures=["rmse"], cv=3)
        gs.fit(data)
        print(gs.best_params["rmse"])
        print(gs.best_score["rmse"])

    def run_opt_vs_unopt(self):
        df_exp = self.df_full.head(n=60000)

        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(df_exp[['user_id', 'business_id', 'stars_y']], reader)

        print("-------------Unoptimized--------------")
        benchmark = []
        results = cross_validate(KNNBaseline(), data, measures=['RMSE'], cv=3, verbose=True)
        tmp = pd.DataFrame.from_dict(results).mean(axis=0)
        tmp = tmp.append(pd.Series([str("KNNBaseline").split(' ')[0].split('.')[-1]], index=['Algorithm']))
        benchmark.append(tmp)
        results = pd.DataFrame(benchmark).set_index('Algorithm').sort_values('test_rmse')
        print(results)

        print("-------------Optimized--------------")
        bsl_options = {'method': 'sgd'}
        sim_options = {'name': 'pearson_baseline', 'min_support': 5, 'user_based': True}
        results = cross_validate(KNNBaseline(bsl_options=bsl_options, sim_options=sim_options), data, measures=['RMSE'],
                                 cv=3, verbose=True)
        tmp = pd.DataFrame.from_dict(results).mean(axis=0)
        tmp = tmp.append(pd.Series([str("KNNBaseline").split(' ')[0].split('.')[-1]], index=['Algorithm']))
        benchmark.append(tmp)
        results = pd.DataFrame(benchmark).set_index('Algorithm').sort_values('test_rmse')
        print(results)

    def find_best_algo(self):
        df_exp = self.df_full.head(n=60000)

        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(df_exp[['user_id', 'business_id', 'stars_y']], reader)

        benchmark = []
        # Iterate over all algorithms
        for algorithm in [KNNBaseline(), KNNBasic(), KNNWithMeans(),
                          KNNWithZScore(), SlopeOne(), NormalPredictor()]:
            # Perform cross validation
            results = cross_validate(algorithm, data, measures=['RMSE'], cv=3, verbose=True)

            # Get results & append algorithm name
            tmp = pd.DataFrame.from_dict(results).mean(axis=0)
            tmp = tmp.append(pd.Series([str(algorithm).split(' ')[0].split('.')[-1]], index=['Algorithm']))
            benchmark.append(tmp)

        results = pd.DataFrame(benchmark).set_index('Algorithm').sort_values('test_rmse')
        print(results)

    def run_scalability_test(self):
        size = 60000
        try:
            reader = Reader(rating_scale=(1, 5))
            benchmark = []
            # Keep increasing size until it fails
            while True:
                print("---------Size of training data: " + str(size) + "-------------")
                df_exp = self.df_full.head(size)
                data = Dataset.load_from_df(df_exp[['user_id', 'business_id', 'stars_y']], reader)
                results = cross_validate(KNNBaseline(), data, measures=['RMSE'], cv=2, verbose=True)
                # Get results & append algorithm name
                tmp = pd.DataFrame.from_dict(results).mean(axis=0)
                tmp = tmp.append(pd.Series([str(KNNBaseline()).split(' ')[0].split('.')[-1]], index=['Algorithm']))
                benchmark.append(tmp)
                results = pd.DataFrame(benchmark).set_index('Algorithm').sort_values('test_rmse')
                print(results)
                # Increase size
                size += 10000

        except Exception as e:
            # won't catch anything here - out of memory so the process will crash
            pass

    def train_models(self):
        dfs = {}
        for i in range(len(self.cities)):
            df = self.df_full.loc[self.df_full['city'] == self.cities[i]].head(60000)
            df.to_csv("df_" + self.cities[i] + ".csv")

            reader = Reader(rating_scale=(1, 5))
            data = Dataset.load_from_df(df[['user_id', 'business_id', 'stars_y']], reader)

            trainset, testset = train_test_split(data, test_size=0.20)

            bsl_options = {'method': 'sgd'}
            sim_options = {'name': 'pearson_baseline', 'min_support': 5, 'user_based': True}
            algo = KNNBaseline(bsl_options=bsl_options, sim_options=sim_options)

            model = algo.fit(trainset)
            pickle.dump(algo, open("trained_model_" + self.cities[i] + ".pkl", 'wb'))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=int, help="Mode of operation")
    args = parser.parse_args()

    mode = args.mode

    e = Experiments()
    if not e.are_data_files_present():
        print("No data files present - begin data load...")
        e.load_data()
        #e.create_city_data()
    else:
        print("Data files present - load from file")
        e.load_pkl_reviews()

    # find best CF algorithm
    if mode == 1:
        e.find_best_algo()

    # find best params for KNNBaseline
    elif mode == 2:
        e.find_best_params()

    # figure out delta for optimized vs unoptimized KNNBaseline
    elif mode == 3:
        e.run_opt_vs_unopt()

    # Scalability - Run this last as it will result in an out of memory error
    elif mode == 4:
        e.run_scalability_test()

    elif mode == 5:
        e.train_models()

    elif mode == 6:
        e.build_sentiment_scores()

    else:
        print("Invalid mode selected")

