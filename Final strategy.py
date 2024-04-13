import pandas as pd
import csv
from datetime import datetime, timedelta
import yfinance as yf
import time

# Function to fetch historical data using yfinance
def fetch_gold_data(symbol, start_date, end_date, interval):
    try:
        gold_data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
        return gold_data
    except Exception as e:
        print(f"Failed to download data for symbol {symbol}: {e}")
        return None

def calculate_ema(data, span):
    alpha = 2 / (span + 1)
    sma = sum(data[:span]) / span
    ema_values = [sma]  # Initialize with the first SMA value
    for i in range(span, len(data)):
        ema = (data[i] - ema_values[-1]) * alpha + ema_values[-1]
        ema_values.append(ema)
    return ema_values

def write_trade_history(trade_history):
    with open('trade_history.csv', mode='a', newline='') as file:
        csv_writer = csv.writer(file)
        for trade in trade_history:
            csv_writer.writerow(trade)
            

def calculate_next_interval():
    current_time = time.localtime()
    current_minute = current_time.tm_min
    current_second = current_time.tm_sec
    remainder = current_minute % 5
    next_minute = current_minute + (5 - remainder) if remainder != 0 else current_minute
    next_interval = (next_minute - current_minute) * 60 + (30 - current_second)
    return next_interval

# Main function
def main():
    # Set the symbol for gold (GC=F for gold futures)
    symbol = 'GC=F'
    # Set the date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)  # Set the initial historical data range

    # Initialize variables for trade execution
    SL = 0
    TP = 0
    profit = 0
    buy = 0
    sell = 0
    time_buy_or_sell = ""

    # Initialize trade history
    trade_history = []

    # print("ema_20 old: ",ema_20)
    # print("ema_10 old: ",ema_10)
    # gold_data['EMA_20'] = [None] * (len(gold_data) - len(ema_20)) + ema_20
    # gold_data['EMA_10'] = [None] * (len(gold_data) - len(ema_10)) + ema_10
    
    # gold_data.to_csv('x.csv')
    
    # ema_20 = calculate_ema(closing_prices[-20:], 20)
    # ema_10 = calculate_ema(closing_prices[-20:], 10)
    # print(closing_prices[-20:])
    # print("ema_20 new: ",ema_20)
    # print("ema_10 new: ",ema_10)
    with open('trade_history.csv', mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["Position","Price","Time"])
        
    while True:
        gold_data = fetch_gold_data(symbol, start_date, end_date, '5m')
        # print(gold_data)
        if gold_data is None:
            # If data fetching fails, wait for a while and retry
            time.sleep(15)  # Wait for a minute before retrying
            continue
        
        closing_prices = gold_data['Close'].values

        all_ema_20 = calculate_ema(closing_prices, 20)
        all_ema_10 = calculate_ema(closing_prices, 10)
        
        ema_20 = all_ema_20[-1]
        ema_10 = all_ema_10[-1]
        print(gold_data.iloc[-1])
        print(ema_20)
        print(ema_10)
        
        if buy == 0 and sell == 0 and ema_20 <= ema_10 and gold_data.iloc[-1]['Low'] <= ema_20 and gold_data.iloc[-1]['Close'] >= ema_10:
            SL = gold_data.iloc[-1]['Low']
            buy = gold_data.iloc[-1]['Close']
            TP = 2 * gold_data.iloc[-1]['Close'] - gold_data.iloc[-1]['Low']
            time_buy_or_sell = gold_data.index[-1]
            trade_history.append(["Buy", buy, time_buy_or_sell])
            
        elif buy == 0 and sell == 0 and ema_20 >= ema_10 and gold_data.iloc[-1]['High'] >= ema_20 and gold_data.iloc[-1]['Close'] <= ema_10:
            TP = 2 * gold_data.iloc[-1]['Close'] - gold_data.iloc[-1]['High']
            SL = gold_data.iloc[-1]['High']
            sell = gold_data.iloc[-1]['Close']
            time_buy_or_sell = gold_data.index[-1]
            trade_history.append(["Sell", sell, time_buy_or_sell])


        if buy > 0:
            if ema_20 >= ema_10:
                flag = 1
                if gold_data.iloc[-1]['High'] >= ema_20 and gold_data.iloc[-1]['Close'] <= ema_10:
                    flag = 0
                elif gold_data.iloc[-1]['High'] >= TP and gold_data.iloc[-1]['Low'] <= TP:
                    flag = 0
                elif gold_data.iloc[-1]['Low'] <= SL and gold_data.iloc[-1]['High'] >= SL:
                    flag = 0
                if flag == 0:
                    SL = 0
                    TP = 0
                    temp_profit = gold_data.iloc[-1]['Close'] - buy
                    profit += temp_profit
                    trade_history[-1].extend([gold_data.iloc[-1]['Close'], gold_data.index[-1], temp_profit])
                    buy = 0

        elif sell > 0:
            if ema_10 >= ema_20:
                flag = 1
                if gold_data.iloc[-1]['Low'] <= ema_20 and gold_data.iloc[-1]['Close'] >= ema_10:
                    flag = 0
                elif gold_data.iloc[-1]['High'] >= SL and gold_data.iloc[-1]['Low'] <= SL:
                    flag = 0
                elif gold_data.iloc[-1]['Low'] <= TP and gold_data.iloc[-1]['High'] >= TP:
                    flag = 0
                if flag == 0:
                    SL = 0
                    TP = 0
                    temp_profit = sell - gold_data.iloc[-1]['Close']
                    profit += temp_profit
                    trade_history[-1].extend([gold_data.iloc[-1]['Close'], gold_data.index[-1], temp_profit])
                    sell = 0

        # Write trade history to CSV file
        write_trade_history(trade_history)
        trade_history = []
        
        next_interval = calculate_next_interval()
        if next_interval < 0:
            next_interval = 5
        time.sleep(next_interval)
        # Update the end_date for the next historical data fetch
        end_date = datetime.now()

if __name__ == "__main__":
    main()