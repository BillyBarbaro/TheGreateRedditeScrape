import sqlite3 as lite
import numpy as np
import math

# Opens the connection to the database containing the reddit posts
con = lite.connect("reddit.db")

with con:
	cur = con.cursor()

	# Gets all the subreddits from the table
	cur.execute("SELECT Name, Posts FROM Subreddit")

	# Lists to hold the various data used for calculating averages
	postMean = []
	postMed = []
	postWordsMed = []
	totCommMed = []
	totCommWordsMed = []

	numSubreddits = 0

	# Loops heads through subreddits
	while True:

		numSubreddits = numSubreddits + 1

		row = cur.fetchone()

		# If there's none left, we stop the loop
		if row == None:
			break
		
		# Gets the name of the table containg the posts in the subreddit
		posts = row[1]

		# We can only access it if it exists
		if not posts == None:

			cur2 = con.cursor()

			# We get the data for all of the posts
			cur2.execute("SELECT Title, Comments FROM " + posts)

			# Arrays to hold the number and length of words in for posts in the subreddit
			postLength = []
			postWordLength = []

			# Arrays to hold the number and length of words for all the comments within the subreddit
			commMed = []
			commWordsMed = []

			# Loops goes through Posts
			while True:
				row2 = cur2.fetchone()

				# If we're out of posts, we step out of the loops and look at another subreddit
				if row2 == None:
					break

				# This is the title of the post
				post = row2[0]

				# Number of words in the post
				postWords = len(post.split())
				postLength.append(postWords)

				# Counts the number of letters in the posts and divides by the number of words to get the average length of a word
				charCountPost = sum((c.isalpha()  for c in post))
				wordLength = charCountPost / postWords
				postWordLength.append(wordLength)

				commentTable = row2[1]

				# If we have a link to a comment table, we take it
				if not commentTable == None:
					cur3 = con.cursor()

					cur3.execute("SELECT Comment FROM " + commentTable)

					# Arrays to keep track of the number and length of words in the comments
					commentLength = []
					wordLength = []

					# Loops goes through Comments
					while True:
						row3 = cur3.fetchone()

						# Makes sure there's still comments to iterate through. If not, we break and go back to posts
						if row3 == None:
							break

						# The comment text
						comment = row3[0]

						# Gets the number of words in the comment
						commentWords = len(comment.split())
						commentLength.append(commentWords)

						# Counts the number of letters in the comment. As long as the comment hasn't been deleted, we can find the average word length for it
						charCountComm = sum((c.isalpha()  for c in comment))
						if (commentWords > 0):
							commentWordLength = charCountComm / commentWords

							wordLength.append(commentWordLength)

					commentLengthMedian = np.median(commentLength)
					wordLengthMedian = np.median(wordLength)

					# As long as we get a real calculation for the median, we save it to a list of comment medians
					if not (math.isnan(commentLengthMedian)):
						commMed.append(commentLengthMedian)
					if not (math.isnan(wordLengthMedian)):
						commWordsMed.append(wordLengthMedian)

			postLengthMedian = np.median(postLength)
			postWordLengthMedian = np.mean(postWordLength)
			commMedMedian = np.mean(commMed)
			commWordsMedMedian = np.median(commWordsMed)

			print(row[0] + "\t" + str(postLengthMedian) + "\t" + str(postWordLengthMedian) + "\t" + str(commMedMedian) + "\t" + str(commWordsMedMedian))
			totCommMed.append(commMedMedian)

			# These verify that the calculations don't come back as NaN. This occurs when we have bad data from the scraping
			if not (math.isnan(commWordsMedMedian)):
				totCommWordsMed.append(commWordsMedMedian)
			if not (math.isnan(postLengthMedian)):
				postMed.append(postLengthMedian)
			if not (math.isnan(postWordLengthMedian)):
				postWordsMed.append(postWordLengthMedian)



	print("Subreddits: " + str(numSubreddits))
	print("Median Words in Post: " + str(np.median(postMed)))
	print("Mean Word Length in Post: " + str(np.mean(postWordsMed)))
	print("Median Words in Comment: " + str(np.median(totCommMed)))
	print("Median Word Length in Comments: " + str(np.median(totCommWordsMed)))