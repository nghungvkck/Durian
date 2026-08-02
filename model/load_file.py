import numpy as np 
import pandas as pd 

path  = "../eda/dataset/audio_features.csv"

class LoadFile:
    def loadFile(self, path) -> pd.DataFrame:
        data = pd.read_csv("path")
        data = data.drop(columns=["file_name", "extract_date", "end_time", "start_time", "peak_mag"])
        return data

