import schedule
import time
from notifier import send_digest_email, should_send_morning, should_send_evening

def morning_job():
    print("Running morning digest...")
    send_digest_email("morning")

def evening_job():
    print("Running evening digest...")
    send_digest_email("evening")

if should_send_morning():
    schedule.every().day.at("08:00").do(morning_job)
    print("Morning email scheduled at 08:00")

if should_send_evening():
    schedule.every().day.at("19:00").do(evening_job)
    print("Evening email scheduled at 19:00")

print("Scheduler running. Press Ctrl+C to stop.")

while True:
    schedule.run_pending()
    time.sleep(60)
    