import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder


def get_data(file="../data/accidents.shz", drop_hour=True):
    # load data
    df = gpd.read_file(file)

    # select features and target columns
    FEATURES_COLS = [
        "HEURE",
        "METEO",
        "ETAT_ROUTE",
        "VITESSE_MA",
        # "LUMIERE",
    ]
    TARGET_COLS = ["BLESSES_LE", "BLESSES_GR", "TUES"]

    # remove rows with missing values in the selected columns
    df = df.loc[:, FEATURES_COLS + TARGET_COLS]
    df.dropna(inplace=True)

    # convert date to datetime
    heure_str = df["HEURE"].str[-6:]
    df["HEURE"] = pd.to_datetime(heure_str, format="%H%M%S").dt.hour

    # encode categorical features
    categorical_cols = df.select_dtypes(include=["object"]).columns
    encoder = OneHotEncoder(sparse_output=False, drop="first")
    encoded_features = encoder.fit_transform(df[categorical_cols])
    encoded_df = pd.DataFrame(
        encoded_features,
        columns=encoder.get_feature_names_out(categorical_cols),
        index=df.index,
    )
    df = pd.concat([df.drop(columns=categorical_cols), encoded_df], axis=1)

    # encode hour in sinus for to avoid the discontinuity between 23h and 0h
    df["HEURE_SIN"] = np.sin(2 * np.pi * df["HEURE"] / 24).round(3)
    df["HEURE_COS"] = np.cos(2 * np.pi * df["HEURE"] / 24).round(3)
    if drop_hour:
        df = df.drop(columns=["HEURE"])

    # add a new column call "VICTIME" which is True if any of the target columns is greater than 0, otherwise False
    df["VICTIME"] = (
        (df["TUES"] > 0) | (df["BLESSES_GR"] > 0) | (df["BLESSES_LE"] > 0)
    ).astype(bool)

    df = df.drop(columns=["TUES", "BLESSES_GR", "BLESSES_LE"])
    return df
