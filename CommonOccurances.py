import sqlite3 as lite
import numpy as np

# Gets rid of punctuation and splits a string so the words can be looked at
def readyString(text):

	text = text.replace(",", "")
	text = text.replace(".", "")
	text = text.replace("!", "")
	text = text.replace("?", "")
	text = text.replace(":", "")
	text = text.replace("-", "")
	text = text.replace("(", "")
	text = text.replace(")", "")
	text = text.replace("[", "")
	text = text.replace("]", "")
	text = text.replace('"', "")
	text = text.replace('@', "")
	text = text.replace('+', "")

	return text.split()

# Gives a count of uncommon words in a string of words
def uncommonCount(words, commonWords):
	uncommon = 0

	for word in words:
		littleWord = word.lower()
		if not ((littleWord in commonWords) or (littleWord[:-1] in commonWords)) and not "'" in littleWord and not "r/" in littleWord:
			if not any(c.isdigit() for c in littleWord):
				uncommon = uncommon + 1

	return uncommon


# Opens the connection to the database containing the reddit posts
con = lite.connect("words.db")

with con:
	cur = con.cursor()

	# Gets all the words from the table
	cur.execute("SELECT Word FROM Common")

	commonWords = cur.fetchall()

# Changes each word from a tuple to a string
for i in range(0, len(commonWords)):
	commonWords[i] = commonWords[i][0]

# Connects to the reddit database
con = lite.connect("reddit.db")

with con:
	cur = con.cursor()

	# Gets all the subreddits from the table and their post table name
	cur.execute("SELECT Name, Posts FROM Subreddit")

	# Keeps the data across subreddits so they can averaged at the end
	postsCommon = []
	commentCommon = []
	while True:

		row = cur.fetchone()

		# If there's none left, we stop the loop
		if row == None:
			break

		# The name of the table containing the posts
		posts = row[1]

		# We can only access it if it exists
		if not posts == None:

			cur2 = con.cursor()

			# We get the data for all of the posts
			cur2.execute("SELECT Title, Comments FROM " + posts)

			# The number of uncommon words
			uncommon = 0.0
			uncommonComments = 0.0

			# The total number of words
			postWordCount = 0
			commentWordCount = 0

			while True:
				row2 = cur2.fetchone()


				# If we're out of posts, we step out of the loops and look at another subreddit
				if row2 == None:
					break

				# This is the title of the post
				post = row2[0]

				# A list of the words in the post
				postWords = readyString(post)

				# The total number of words in titles on a given subreddit
				postWordCount = postWordCount + len(postWords)

				# The total of uncommon words in titles on a given subreddit
				uncommon = uncommon + uncommonCount(postWords, commonWords)

				# The name of a comment table for a post
				commentTable = row2[1]

				# If we have a link to a comment table, we take it
				if not commentTable == None:
					cur3 = con.cursor()

					cur3.execute("SELECT Comment FROM " + commentTable)

					# Loops goes through Comments
					while True:
						row3 = cur3.fetchone()

						# Makes sure there's still comments to iterate through. If not, we break and go back to posts
						if row3 == None:
							break

						# The comment text
						comment = row3[0]

						# A list of words in the comment
						commentWords = readyString(comment)

						# The total number of words in comments in a given subreddit
						commentWordCount = commentWordCount + len(commentWords)

						# The total count of uncommon words in comments in a given subreddit
						uncommonComments = uncommonComments + uncommonCount(commentWords, commonWords)



				
			# Prints out the data for us to look at in terminal (Eventually could put this in a db I suppose)
			if (postWordCount > 0 and commentWordCount > 0):
				print(row[0] + ": " + str(uncommon/postWordCount) + "\t" + str(uncommonComments/commentWordCount))
				postsCommon.append(uncommon/postWordCount)
				commentCommon.append(uncommonComments/commentWordCount)



	# Calculates some averages for comparison purposes
	print("Median Uncommon Post Percentage: " + str(np.median(postsCommon)))
	print("Median Uncommon Comment Percentage: " + str(np.median(commentCommon)))




