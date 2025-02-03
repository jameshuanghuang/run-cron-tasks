import yfinance as yf
import pandas as pd
import logging
import csv
import requests
import re
import os
import random

logging.basicConfig(level=logging.INFO, filename='status.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def job1():
    try:
        df = pd.read_csv('./output/crypto/BTC.csv', index_col=0, parse_dates=True)
    except FileNotFoundError:
        df = pd.DataFrame()

    BTC = yf.Ticker('BTC-USD')

    if df.empty:
        btc_data = BTC.history(period='max')
        with open('./output/crypto/BTC.csv', mode='a', newline='') as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(['Date'] + btc_data.columns.to_list())

            for date, row in btc_data.iterrows():
                writer.writerow([date.strftime('%Y-%m-%d %H:%M:%S%z')] + row.tolist())
            
        logger.info(f"Created .csv file. Pulled max history.")
        return
    else:
        start_date = df.index[-1] + pd.DateOffset(days=1)
        cur_date = pd.Timestamp.today().tz_localize('UTC')

        if start_date < cur_date:
            # btc_data = BTC.history(period='1D')
            btc_data = BTC.history(start=start_date) # # [,)
            cnt = btc_data.shape[0]
            with open('./output/crypto/BTC.csv', mode='a', newline='') as file:
                writer = csv.writer(file)

                for date, row in btc_data.iterrows():
                    writer.writerow([date.strftime('%Y-%m-%d %H:%M:%S%z')] + row.tolist())

            logger.info(f"Appended {cnt} rows to data starting from {btc_data.index[0].date()} to {btc_data.index[-1].date()}.")
        else:
            logger.info(f"Data is up to date.")

def job2():
    response = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false')
    response = response.json()

    BTCCap = 0
    altCap = 0
    current_time = pd.Timestamp.today().tz_localize('UTC').strftime('%Y-%m-%d %H:%M')

    for x in response:
        if x['id'] == "bitcoin": #adds bitcoin market cap to BTCCap and altCap
            BTCCap = x['market_cap']
            altCap = altCap + x['market_cap']
        else: #adds any altcoin market cap to altCap
            altCap = altCap + x['market_cap']

    with open("./output/crypto/BTC.D.csv", mode='a+', newline ="") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow([current_time,"{:.2f}".format((BTCCap/altCap)*100)])
    
    logger.info(f"BTC.D data is up to date.")

def fetch_option_chain_with_retry(ticker, expiry, max_retries=3, timeout=30):
    attempts = 0
    while attempts < max_retries:
        try:
            option_chain = ticker.option_chain(expiry)
            return option_chain  # Return the data if successful
        except Exception as e:
            attempts += 1
            logger.error(f"Attempt {attempts} failed for expiry {expiry} of ticker {ticker.ticker}. Error: {e}")
            if attempts < max_retries:
                time.sleep(5)  # Wait for 5 seconds before retrying
            else:
                logger.error(f"Max retries reached for {expiry}. Moving to the next expiry.")
                raise  # Re-raise exception if max retries are exceeded

def job3(inputTicker):
    ticker = yf.Ticker(inputTicker)
    expiry_dates = ticker.options

    df_call_list = []
    # df_put_list = []

    for expiry in expiry_dates:
        try:
            option_chain = fetch_option_chain_with_retry(ticker, expiry)  # Using the retry function
            # Append call and put options data to respective lists
            option_chain.calls['expiry'] = expiry
            # option_chain.puts['expiry'] = expiry

            df_call_list.append(option_chain.calls)
            # df_put_list.append(option_chain.puts)
        
        except Exception as e:
            logger.error(f"Failed to fetch data for expiry {expiry} of ticker {inputTicker}. Skipping this expiry.")
            continue  # Skip the current expiry if error occurs and proceed to the next one

    # Concatenate all the dataframes into one
    df = pd.concat(df_call_list, axis=0)
    # df_put = pd.concat(df_put_list, axis=0)
    # df = pd.concat([df_call, df_put], axis=0)

    # Drop unnecessary columns
    df.drop(['change', 'percentChange', 'contractSize', 'currency'], axis=1, inplace=True)

    # Extract option type from the contract symbol
    df['optionType'] = df['contractSymbol'].apply(
        lambda x: re.match(r'([A-Za-z]+)(\d{6})([CP])(\d+)', x).group(3)  # Use group(3) to get the option type
    )

    # Sort by relevant columns
    df.sort_values(
        by=['optionType', 'expiry', 'strike'],
        ascending=[True, True, True],
        inplace=True
    )

    # Save the data to CSV
    today = pd.Timestamp.today().tz_localize('UTC').strftime('%Y-%m-%d')
    df.to_csv(f"./output/options/{today}/OMON_{inputTicker}_{today}.csv", index=False)

    logger.info(f"{inputTicker} option data is up to date.")

def job4():
    logger.info(f"Get tickers from watchlist.")

    # Mimic getting tickers from watchlist.
    watch_lists = [
        ['QQQ', 'MSTR', 'PLTR', 'NVDA', 'VST', 'GOOG', 'SOFI'],
        ['LUCK', 'SPOT', 'LMND', 'KW'],
        []
    ]
    prob = [1.0, 0.0, 0.0]
    
    # Use watch_lists as values and prob for selection
    watch_list_selected = random.choices(watch_lists, prob)[0]

    if watch_list_selected:
        logger.info(f"Fetched watchlist: {watch_list_selected}")
        return watch_list_selected
    else:
        logger.info(f"Watchlist is empty")

def job5():
    # Subscriber data
    subscribers = {
        'Jason': {
            'email': 'jason.k@gmail.com',
            'watchlist': ['AMZN', 'O']
        },
        'Arron': {
            'email': 'arron.r@example.com',
            'watchlist': ['MSTR', 'GOOG']
        },
        'Mike': {
            'email': 'mike.m@example.com',
            'watchlist': ['TSLA']
        },
        'Elaine': {
            'email': 'elaine.e@example.com',
            'watchlist': ['AAPL', 'MSTR']
        },
        'Sofia': {
            'email': 'sofia.s@example.com',
            'watchlist': ['AMZN', 'MSFT']
        }
    }

    unusual_option_activity = ['MSTR']

    for subscriber, details in subscribers.items():
        # Check if subscriber has a watchlist and email
        if 'watchlist' in details and details['watchlist']:
            # Check if any of the unusual activity is in the subscriber's watchlist
            for stock in unusual_option_activity:
                if stock in details['watchlist']:
                    # Send email
                    email = details['email']
                    logger.info(f"Sending email to {email} about unusual option activity in {stock}")
                    # send_email(email, stock)

try:
    API_KEY = os.environ["API_KEY"]
except KeyError:
    API_KEY = "secret_api_key_empty"

if __name__ == "__main__":
    logger.info(f"API_KEY: {API_KEY}")
    # https://www.python-engineer.com/posts/run-python-github-actions/

    today = pd.Timestamp.today().tz_localize('UTC').strftime('%Y-%m-%d')
    crypto_path = 'output/crypto/'
    option_path = f'output/options/{today}'
    
    if not os.path.exists(crypto_path):
        os.makedirs(crypto_path)
    
    if not os.path.exists(option_path):
        os.makedirs(option_path)

    job1()
    job2()

    watch_list = job4()
    if watch_list:
        for ticker in watch_list:
            job3(ticker)
    job5()