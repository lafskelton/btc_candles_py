# coinbase_candles
##### This library is a quick solution to fetching bitcoin candle data from coinbase in an extendable and portable way. Data is fetched and converted into a list of numpy arrays or a pandas DataFrame. I will be adding torch support and extensions for RSI, MA, and a few other datapoints.

### basic usage
```
from coinbase_candles import CoinbaseCandles
from datetime import datetime
import numpy as np

dataset = CoinbaseCandles(
    symbol="BTC-USDC",
    start_time=datetime(year=2024, month=7, day=11, hour=11, minute=11)
)

# update the dataset. this will load all candles from start_time until runtime for your specified symbol. 
dataset.update()

#access indicators. 
open_data: np.ndarray[np.float32] = dataset.indicator("open")

#save to disk
dataset.to_csv()

#DataFrame
dataset.to_df()
```
