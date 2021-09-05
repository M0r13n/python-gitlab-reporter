import os

from reporter.core import Reporter

Reporter.init("https://gitlab.com", private_token=os.environ.get("TOKEN"), project_id=23234375)

if __name__ == "__main__":
    # Assume you are doing something great
    x = [1, 2, 3]
    x[4]  # Oh noo!
