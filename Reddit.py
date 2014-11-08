import requests
from pyquery import PyQuery
import time
import json
import re
import sqlite3 as lite

# Given a URL, creates a PyQuery object for that page
def getUrlQuery(url):
	# Stops reddit from identifying the script as a bot
	headers = {'User-agent' : 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25'}
	response = requests.get(url, headers = headers)
	html = response.text
	response.close()
	return PyQuery(html)

# Constructs a url for the top posts of the week on given a subreddit.  Returns a PyQuery object of that page
def getSubreddit(subReddit):
	url = 'http://www.reddit.com/r/' + subReddit + '/top/?sort=top&t=week'
	return getUrlQuery(url)

# Takes a post and outputs the user, title, number of comments and date of the post to the output file
def writePostData(post, subredditId):
	# The author data is contained in an anchor tag of class .author.may-blank.id the id is random but no other tag of this type exist within the div
	author = post.find('.author.may-blank').text()

	# The title is contained in an anchor tag of class .title.may-blank.
	title = post.find('.title.may-blank').text()

	# The number of comments is contained in the anchor tag of the class shown below. If there are no comments yet, the text simply reads "comment", so we can say there's no comments
	text = post.find('.comments.may-blank').text()
	if (text == "comment"):
		text = "0 comments"

	print(title)

	# Grabs the date from the time tag. Occasionally, there were multiple tags, so we just grab the first one seen and takes its title which is a nicely formatted date
	date = post.find('time').eq(0).attr('title')

	# Connects to the database
	con = lite.connect("reddit.db")

	with con:

		cur = con.cursor()

		# Inserts the data into the table
		cur.execute("INSERT INTO Posts(User, Title, Comment_Count, Date, Subreddit) VALUES(?, ?, ?, ?, ?)", (author, title, text, date, subredditId))

		return cur.lastrowid


# Takes a comment (formatted in HTML) and writes out the user, votes it has, date, and the comment itself
def writeCommentDataHTML(group, postId):
	# Grabs the author of the comment (at index 0 because it is included twice, once for collapsed and once for uncollapsed)
	author = group.find('.author.may-blank').eq(0).text()
	# Finds the number of points for a given comment
	score = group.find('.tagline').find('.score.unvoted').text()
	# The title of the time tag has the date nicely formatted
	date = group.find('.tagline').find('time').attr('title')
	# .md is the class of the div acutally containing the comment
	comment = group.find('.md').text()

	print(comment)

	# Finds the comment table that would correspond to this comment "(subreddit)_(commentNumber)_Comments"
	con = lite.connect("reddit.db")

	with con:

		cur = con.cursor()

		# Inserts the comment into the table
		cur.execute("INSERT INTO Comments(User, Points, Date, Comment, Post) VALUES(?, ?, ?, ?, ?)", (author, score, date, comment, postId))


# Takes a comment (formatted in JSON) and writes out the user, votes it has, date, and the comment itself
def writeCommentDataJSON(comment, postId):

	# This loads the data that is turned into HTML included in the JSON file
	raw = comment['data']['content']

	# In each case we check to assure it's not NoneType because occasionally comments are deleted

	author = ""
	points = ""
	date = ""
	commentText = ""

	# Finds the author within the content
	findAuthor = re.search(r'http://www.reddit.com/user/(.*?)"', raw)
	if not (findAuthor == None):
		author = findAuthor.group(1)

	# Finds the number of points a comment has
	findPoints = re.search(r'class="score unvoted"&gt;(.*? point[s]?)&lt', raw)
	if not (findPoints == None):
		points = findPoints.group(1)

	# Finds the date at which a comment was posted
	findDate = re.search(r'time title="(.*?)"', raw)
	if not (findDate == None):
		date = findDate.group(1)

	# The comment text is nicely included as a dictionary entry
	commentText = comment['data']['contentText']

	print(commentText)

	con = lite.connect("reddit.db")

	with con:

		cur = con.cursor()

		# Inserts the comment into the table
		cur.execute("INSERT INTO Comments (User, Points, Date, Comment, Post) VALUES(?, ?, ?, ?, ?)", (author, points, date, commentText, postId))


# Generates the HTTP request for more comments given the current page and the javascript call it's supposed to make
def generateRequest(link, loadMore):

	# The header of the request. The variable link is just the current page. Passed in as an argument of the function
	headers = {'Accept' : 'application/json, text/javascript, */*; q=0.01',
		'Origin' : 'http://www.reddit.com',
		'Referer' : link,
		'X-Requested-With' : 'XMLHttpRequest',
		'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14',
		'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8'}

	# Pulls the id, but we must extract the phrase "more_" appended to the beginning
	idAttr = loadMore.attr('id')
	searchId = re.search(r'more_(.*)', idAttr)
	myId = searchId.group(1)

	# Gets the javascript function call
	arguments = loadMore.attr('onclick')
	# Grabs the argumnets from the function we need to use in the request
	searchArgs = re.search("'(t3_.*?)', '(.*?)'", arguments)

	linkId = searchArgs.group(1)			
	children = searchArgs.group(2)

	# Data dictionary for the request
	data = {'link_id' : linkId,
			'children' : children,
			'depth' : 0,
			'id' : myId,
			'pv_hex' : '',
			'r' : subreddit,
			'renderstyle' : 'html'}


	return headers, data

# Using the javascript function call from the JSON file, we modify our request to get the next set of comments
def modifyRequest(raw, data):
	findMyID = re.search(r'id="more_(.*?)"', raw)
	myId = findMyID.group(1)

	findLinkID = re.search(r"this, '(.*?)'", raw)
	linkId = findLinkID.group(1)

	findChildren = re.search(r"', '(.*?)'", raw)
	children = findChildren.group(1)

	# Changes the values in the request dictionaries
	data['link_id'] = linkId
	data['children'] = children
	data['id'] = myId


# Makes the HTTP request for more comments
def loadMoreComments(headers, data):

	# Makes the request to the server which returns the JSON file of the new data
	moreComments = requests.post("http://www.reddit.com/api/morechildren", data=data, headers=headers).text
	moreComments = json.loads(moreComments)

	# Gets us to the List of relevant information within the returned JSON file
	return moreComments['jquery'][14][3][0]

# Given a PyQuery object of a subreddit, gets the number of subscribers and users online
def subredditInfo(d):

	# This query returns the two spans containg the subscribers and active users
	num = d('.number')

	# Grabbing the text gives us just the two numbers. The first being subscribers and the second the number of users
	num = num.text().split()

	con = lite.connect("reddit.db")

	with con:
		cur = con.cursor()

		# Uncomment the below lines to start a new table
		#cur.execute("DROP TABLE IF EXISTS Subreddit")
		#cur.execute("DROP TABLE IF EXISTS Posts")
		#cur.execute("DROP TABLE IF EXISTS Comments")

		#cur.execute("CREATE TABLE Subreddit(Id INTEGER PRIMARY KEY, Name TEXT, Subscribers INT, Active INT, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(Name))")
		#cur.execute("CREATE TABLE Posts(Id INTEGER PRIMARY KEY, User TEXT, Title TEXT, Comment_Count INT, Date TEXT, Subreddit INT)")
		#cur.execute("CREATE TABLE Comments(Id INTEGER PRIMARY KEY, User TEXT, Points TEXT, Date TEXT, Comment TEXT, Post INT)")

		# Insert the subreddit into the database
		cur.execute("INSERT OR REPLACE INTO Subreddit2(Name, Subscribers, Active) VALUES(?, ?, ?)", (subreddit, int(num[0].replace(',','')), int(num[1].replace(',','').replace('~', ''))))
		return cur.lastrowid

# Outputs a specified number of top weekly posts for a given page. Also calls for their comments if specified
def subredditPosts(d, subredditId, numPosts, numComments):

	count = 0
	while True:

		# Gets all blocks of HTML of class .entry.unvoted. They're the divs containing each post
		posts = d('.entry.unvoted')

		# We loop through each of these blocks and parse the data we want
		for post in posts.items():

			count = count + 1
			# Takes the data in the post and outputs it to the file
			postId = writePostData(post, subredditId)
			# If the user has requested comments, we go and look for those
			if (numComments > 0):
				# This finds the url for the comments page from the anchor tag leading there.
				link = post.find('.comments.may-blank').attr('href')

				# Generates a PyQuery object for the comments page
				linkQuery = getUrlQuery(link)

				# Calls the function to get the comments
				subredditComments(linkQuery, link, numComments, postId)

				# Uncomment line below if get 429 error meaning we're making too many requests in too short of time period
				#time.sleep(2)

			# We decrement the amout of posts we still need. If we've scraped as many as we need, the method returns
			#numPosts = numPosts - 1
			#if numPosts == 0:
			if count == numPosts:
				return

		# If we reach this point in the code, we've grabbed all the posts on a page and to load the next page to get more
		# We check to make sure there's a button for another page
		if (d.hasClass('nextprev')):
			# A flag to see if we get a new page
			changed = False
			# Gets the the anchor tags for the buttons leading to the last and previous pages
			nextPages = d('.nextprev').find('a')
			for page in nextPages.items():
				# We check to see if the link points to the next page (as opposed to prev)
				rel = page.attr('rel')
				if rel == "nofollow next":

					# Uncomment line below if get 429 error meaning we're making too many requests in too short of time period
					#time.sleep(2)

					# If it does, we follow that link and flip the flag to show we've found more posts
					d = getUrlQuery(page.attr('href'))
					changed = True

			# If we didn't find another page, we let they user know they've over-requested
			if not changed:
				return
		# If there's only one page of posts, we can't load more
		else:
			return


# Grabs the specified number of top-level comments from a post. Inputs are a PyQuery object of the page, the link to the page, and the number of comments desired
def subredditComments(d, link, numComments, postId):

	# Grabs all the blocks of comments (This includes ones that are not top-level and some other blocks as well), but no better identifiers could be found
	groups = d('.entry.unvoted')

	# Loops through every block of the class above
	for group in groups.items():

		# Filters the blocks, specifiying that at no point can it be a child of anyting (top-level) and that it must be one within the comment table.  The last statement was added becasue the "load more" button is techincall an entry, but contains no date entry
		if (len(group.parents('.child')) == 0 and not len(group.parents('.sitetable.nestedlisting')) == 0 and not group.find('.tagline').find('time').attr('title') == None):

			# Takes the group and extracts the relevant information, writing it to the output file
			writeCommentDataHTML(group, postId)

			# Decrements the number of comments we still need to load. If we've got enough, returns
			numComments = numComments - 1
			if numComments == 0:
				return

	# Now we handle the case if we need more comments then were initially on the page
	# This is done through an AJAX request that returns a JSON file, so we must generate this request then parse the JSON

	# The javascript call inclues a handfull of arguments we must parse and include in the requests. All the links loading to more comments are of the class
	nextComment = d('.morecomments')
	length = len(nextComment)
	# We need to make sure there are more comments to load
	if not (length == 0):
		# If we're going to load more comments (as opposed to loading more replies to a commnet), the link will be the last one on the page
		loadMore = nextComment.eq(length - 1).find('a')
		# Here we check that the last one is not a load more replies. If it is, it will be the child of something
		if (len(loadMore.parents('.child')) == 0):

			# Getst the dictionaries for the requests
			headers, data = generateRequest(link, loadMore)

			# We continue to read and load more comments until we have the specified amount or we run out of comments
			while True:
				
				# Makes the HTTP request and gets the relevant information from the JSON file (in this case, a list of dictionaries)
				commentList = loadMoreComments(headers, data)

				# For each entry in the list, we extract the required data
				for comment in commentList:
					# First we make sure it's a top level comment by assuing it is the correct kind and it's parent is the link ID
					if (comment['kind'] == 't1' and comment['data']['parent'] == data['link_id']):
						
						# Extracts relevant information and writes it out to the output file
						writeCommentDataJSON(comment, postId)

						# Decrements the number of comments and if we don't need any more, returns
						numComments = numComments - 1
						if numComments == 0:
							return

				# Here we've looped through all avaliable comments in the JSON file and need to request more. This request is within the last entry in the list
				if (len(commentList) > 0):
					more = commentList[-1]
					# We check to see if the last entry has more comments available.
					if (more['kind'] == 'more' and more['data']['parent'] == data['link_id']):

						# We grab the content and parse through it to find the same data we did above, only this time in JSON
						raw = more['data']['content']

						# Extracts the information from the javascript fall to modify the request dictionary
						modifyRequest(raw, data)
						
					# If there aren't more comments available, we let the user know and return
					else:
						return
				# There's no comments on the current page, we exit
				else:
					break

def scrapeReddit(subreddit, posts, comments):
	# Returns a PyQuery object with the contents of the page for the top posts of the week on the given subreddit
	d = getSubreddit(subreddit)

	# Grabs the number of subscribers and active users on the subreddit
	subredditId = subredditInfo(d)
	
	# If they've resquested posts, we'll go find those and possibly comments too
	if (posts > 0):
		subredditPosts(d, subredditId, posts, comments)


# Prompts the user to give the subreddit they wish to look at and how many of the top posts from the week they want
subreddit = raw_input("Enter the name of a subreddit: ").lower().replace(" ", '')
posts = raw_input("Enter the number of posts you wish to retrieve: ")

# If no posts are entered, it is assumed to be 0
if (posts == ''):
	posts = 0
else:
	posts = int(posts)

comments = 0

# If they have asked for a number of posts, they can also choose to display as many comments as they choose
if (posts > 0):
	comments = raw_input("Enter the number of top level comments you wish to retrieve: ")

	if (comments == ''):
		comments = 0
	else:
		comments = int(comments)

scrapeReddit(subreddit, posts, comments)

