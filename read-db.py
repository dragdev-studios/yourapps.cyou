import sys
import sqlite3
try:
    from tabulate import tabulate
except ImportError:
    print("You need to install tabulate.")
    sys.exit(4)

values = []


with sqlite3.connect("./data.base") as connection:
    connection.row_factory = sqlite3.Row  # we have to set this to be able to get key,value pairs.
    for row in connection.execute(
        """SELECT * FROM referrers ORDER BY referrals DESC;"""
    ):
        values.append(tuple(row))

print(tabulate(values, tablefmt="psql"))
