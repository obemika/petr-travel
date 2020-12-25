import numpy as np
import pandas as pd

from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics.pairwise import haversine_distances
from math import radians

EARTH_RADIUS = 6370


# class ProxyModel:
#     def __init__(self):
#         pass
#
#     def predict(self):
#         pass
#
#     def predict_proba(self):
#         pass
#
#     def fit(self, X_train, y_train):
#         pass

class PetrModel:
    def __init__(self, dataset: pd.DataFrame, world: pd.DataFrame):
        self.data = dataset.drop(columns=['HDI'])
        self.countries = self.data['Country'].values
        country_df = world.loc[world['name'].isin(self.countries)][['name', 'geometry']].set_index('name')
        country_poly_centers = {country: country_df.loc[country].geometry.centroid \
                                for country in country_df.index.values}
        self.country_poly_centers = country_poly_centers

    @classmethod
    def load_data(cls, dataset_filepath):
        return pd.read_csv(dataset_filepath, sep=";", index_col=0)

    def create_model(self, sea, flight_time, country_start, countries_ban):
        prepared_data = self.prepare_dataset(sea, flight_time, country_start, countries_ban)
        num_of_neighbors = min(len(prepared_data), 5)
        knn = KNeighborsClassifier(n_neighbors=num_of_neighbors, metric="manhattan")
        X = prepared_data.loc[:, prepared_data.columns != 'Country']
        y = prepared_data.loc[:, prepared_data.columns == 'Country']
        knn.fit(X, y)
        self.model = knn

    @staticmethod
    def prepare_query(query: list) -> list:
        sea, winter, spring, summer, autumn, sightseeing, cat_dog, exotic, hours = query
        sightseeing = (sightseeing - 1) / (10 - 1)
        exotic = (exotic - 1) / (10 - 1)
        distance = (hours - 1) / (12 - 1)
        query = sea, winter, spring, summer, autumn, sightseeing, cat_dog, exotic, distance
        return query

    def prepare_dataset(self, sea, flight_time, country_start, countries_ban):
        data = self.data[~self.data['Country'].isin(countries_ban + [country_start])]
        assert len(data) > 0
        distances = [haversine_distances([[radians(self.country_poly_centers[country].y),
                                           radians(self.country_poly_centers[country].x)],
                                          [radians(self.country_poly_centers[country_start].y),
                                           radians(self.country_poly_centers[country_start].x)]
                                          ]) for country in data['Country'].values]
        distances = np.array(distances).max(axis=(1, 2)) * EARTH_RADIUS
        data['Distance'] = distances
        data['Sightseeing (0 - 10)'] = data['Sightseeing (0 - 10)'] / 10
        data['Exotic'] = data['Exotic'] / 10
        min_dist, max_dist = data['Distance'].min(), data['Distance'].max()
        data['Distance'] = (data['Distance'] - min_dist) / (max_dist - min_dist)
        data = data.loc[
                        (data['Distance'] <= 1 + (flight_time - 1) / (12 - 1))
                        & (data['Sea'] == sea)
                       ]
        return data

    # sea, winter, spring, summer, autumn, sightseeing, cat_dog, exotic, hours = query
    def predict(self, country_start, countries_ban, query, top_k_countires=3, im_lucky=False) -> np.array:
        if im_lucky:
            top_countries = np.random.choice(self.model.classes_, 1 + top_k_countires, replace=False)
            top_1, *others = top_countries
            return top_1, others
        else:
            try:
                sea = query[0]
                filght_time = query[8]
                self.create_model(sea, filght_time, country_start, countries_ban)
            except AssertionError:
                return None, []
            query = PetrModel.prepare_query(query)
            top_1 = self.model.predict([query])[0]
            preds = self.model.predict_proba([query])
            preds = list(map(lambda x: True if x > 0 else False, preds.ravel()))
            others = list(self.model.classes_[preds])
            others.remove(top_1)
            sample_size = min(len(others), top_k_countires)
            return top_1, np.random.choice(others, sample_size, replace=False)









