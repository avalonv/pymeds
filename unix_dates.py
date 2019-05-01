import datetime
import time

date_today = round(time.time())

def print_date(timestamp):
    print(timestamp)
    print(datetime.date.fromtimestamp(timestamp))

def increase_date(timestamp):
    return timestamp + 86400

def decrease_date(timestamp):
    return timestamp - 86400

while True:
    choice = input('>  ')
    if choice == '+':
        date_today = increase_date(date_today)
    if choice == '-':
        date_today = decrease_date(date_today)
    print_date(date_today)

