# legit-latency

@@@written in Python 2@@@

Utilizes NASDAQ's Data on Demand API to extract trade data for two stocks given their tickers, a market center code, and a time interval. This trade data is used to determine a baseline latency between the two market centers by way of cross-correlation (which could be made more efficient). From there, we can observe other data between the same market centers and detect possible instances of light-speed insider trading if a specific trade occurs faster than our determined baseline latency.
