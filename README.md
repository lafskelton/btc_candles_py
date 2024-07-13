# coinbase_candles_py
##### This library is a quick solution to fetching bitcoin candle data from coinbase in an extendable and portable way. Data is fetched and converted into a list of numpy arrays or a pandas DataFrame. I will be adding torch support and extensions for RSI, MA, and a few other datapoints.

### basic usage
```
from candles import BitcoinCandles
from datetime import datetime

COINBASE_API_VERSION = "/api/v3"

dataset = BitcoinCandles(
    start_time=datetime(year=2024, month=7, day=11, hour=11, minute=11)
)

#load more data. (300 is max that coinbase will allow. will do nothing if future date specified)
dataset.load_more_candles(300)

#access indicators. 
open_data: np.ndarray[np.float32] = dataset.indicator("open")

#save to disk
dataset.to_csv()

#DataFrame
dataset.to_df()
```
