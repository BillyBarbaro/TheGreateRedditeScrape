import requests
from pyquery import PyQuery
import sqlite3 as lite

# Access a site listing the 5000 most common words in the English Language
headers = {'User-agent' : 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25'}
response = requests.get("http://www.englishclub.com/vocabulary/common-words-5000.htm", headers = headers)
html = response.text
response.close()

d = PyQuery(html)

# Each words is contained within an <li> tag
words = d("li")

# Open the database
con = lite.connect("words.db")

with con:
	cur = con.cursor()

	# Uncomment the below lines to start a new table
	#cur.execute("DROP TABLE IF EXISTS Common")
	#cur.execute("CREATE TABLE Common(Id INTEGER PRIMARY KEY, Word TEXT)")

# Loops through all the <li> tags on a page and drops its contents into the SQL Table
for word in words.items():
	cur.execute("INSERT INTO Common(Word) VALUES (?)", (word.text().lower(),))
	print(word.text())

# Commits the changes
con.commit()