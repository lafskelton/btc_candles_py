import numpy as np
from datetime import datetime, timedelta
import http.client
import json
import pandas as pd 
import os 

# W I P # 
# Enables incrementally fetching Bitcoin candle data from the CoinBase API formatted into workable numpy arrays.
# outputs to df and csv. extendable.


COINBASE_URL = "api.coinbase.com"
COINBASE_API_VERSION = "/api/v3"

BUFFER_EXPAND_SIZE = 3600
BUFFER_EXPAND_THRESHOLD = 60

# Portable class to store and extend candle data
class CandleData: 
    # params
    _ncandles = 0 # also acts as cursor
    _buffsz = 0
    # data
    data: dict[str, np.ndarray[np.float32]] = {
        "open": np.array([], dtype=np.float32),
        "close": np.array([], dtype=np.float32),
        "high": np.array([], dtype=np.float32),
        "low": np.array([], dtype=np.float32),
        "volume": np.array([], dtype=np.float32)
    }

    def _auto_expand(self):
        # if there is less than 60 minutes worth of space or buffsz is zero, resize the arrays to add an aditional day of space.
        if(self._ncandles >= self._buffsz - BUFFER_EXPAND_THRESHOLD):
            try:
                self._buffsz += BUFFER_EXPAND_SIZE
                for key in self.data.keys():
                    self.data[key].resize((self._buffsz + BUFFER_EXPAND_SIZE))
                return
            except:
                print("failed to expand array!")
                return

    def __init__(self):
        # calling this when buffersize is set to zero will cause it to allocate space :)
        self._auto_expand()
        return

    def add_candle(self, data:dict[str, np.float32]):
        self._auto_expand()
        for key in data.keys():
            if key in self.data.keys():
                self.data[key][self._ncandles] = data[key]     
        self._ncandles += 1
        return
    
    def to_df(self) -> pd.DataFrame:
        try:
            df = pd.DataFrame([x[1] for x in self.data.items()]).transpose()
            df.columns = ["open", "close", "high", "low", "volume"]
            return df[(df.T != 0).any()]
        except:
            print("unable to convert CandleData into pandas.DataFrame")
            exit()  

# This class calls the coinbase API, retrieves a range of candles, and outputs those candles in a nicer way.
class CoinbaseCandles(CandleData):
    # connection 
    conn: http.client.HTTPSConnection

    #parameters
    GRANULARITY = "ONE_MINUTE"
    symbol: str
    start_time: datetime
    candles_loaded = 0

    downloading = False

    def __init__(self, symbol: str, start_time: datetime):
        self.symbol = symbol
        self.start_time = start_time
        try:
            self.conn = http.client.HTTPSConnection(COINBASE_URL)
        except:
            print(f"Unable to connect to coinbase API at {COINBASE_URL}")
            exit(1)

        print(f"Connected to coinbase API at {COINBASE_URL}")


    # returns the date of the next candle that comes after the candles we have already loaded
    def _get_cursor_start_time(self,) -> datetime:
        return self.start_time + (timedelta(minutes=1) * self.candles_loaded)
    
    def load_more_candles(self, ncandles: int) -> object:
        # calc params
        cursor_time = self._get_cursor_start_time()
        end_time =  self._get_cursor_start_time() + (timedelta(minutes=1) * (ncandles-1))
        self.candles_loaded += ncandles
        
        # fetch
        try: 
            self.conn.request(
                "GET", f"{COINBASE_API_VERSION}/brokerage/market/products/{self.symbol}/candles?start={int(cursor_time.timestamp())}&end={int(end_time.timestamp())}&granularity={self.GRANULARITY}", 
                '', 
                {'Content-Type': 'application/json'}
            )
        except:
            print("unable to fetch new data!")
            return {}
        
        # decode
        try:
            req = self.conn.getresponse().read().decode('utf-8')            
            decoder = json.decoder.JSONDecoder()
            data =  decoder.decode(req)
            #
            if "candles" in data.keys() and len(data['candles']) == 0: 
                if self.downloading:
                    self.downloading = False
                    return
                print("coinbase returned no candles, maybe the date requested is wrong?")
                return
            if 'error' in data.keys():
                print("request error: ", data['error'])
                return
        except:
            print("unable to decode new data!\n")
            print("\n")
            return {}

        # append data. this would be okay in C. the CPU would likely load the target array in cache ahead of time and the compiler would likely wipe away overhead.
        #              what happens in python? no clue, all I know is that it is probably faster to compile, execute, and run the C equiv.
        for candle in data['candles']:
            self.add_candle(
                {
                    "open": float(candle['open']),
                    "close": float(candle['close']),
                    "high": float(candle['high']),
                    "low": float(candle['low']),
                    "volume": float(candle['volume']),
                }
            )
        print(f"Fetched {ncandles} additional bitcoin candles (total: {self._ncandles})")


    def update(self,):
        print(f"updating {self.symbol} dataset!")
        # download any data required to satisfy the buffer containing all data from start_date until now.
        self.downloading = True
        while self.downloading:
            self.load_more_candles(300)
        return

    def indicator(self, key: str) -> np.ndarray[np.float32]:
        if key in self.data.keys():
            return self.data[key][0:self._ncandles]
        #
        print("ERROR: unable to find indicator", key)
        return []
    
    def to_csv(self):
        if not os.path.isdir("data"):
            os.mkdir("data")
        self.to_df().to_csv(f"data/{int(self.start_time.timestamp())}-{int(self._get_cursor_start_time().timestamp())}.csv", index_label="id")
        print(f"Saved {self._ncandles} bitcoin candles to CSV")
