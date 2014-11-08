The Great Reddit eScrape
==========

A Python script I wrote to script allowing the user to specify a subreddit.  Then asks them the number of top posts of the week and top level posts for those comments they wish to scrape.  Saves the data into a sqlite database titled reddit.db.  Also includes a couple scripts for analysis of the data.

## Reddit

The script to be run to do the scraping

## RedditCreative

Runs a script across the database and presents the user with statistics on the number of words and word length in posts.

## CommonWords

Populates the words.db with the 5000 most common words in the English language for the next anaylysis script

## CommonOccurances

Takes the scraped data and calculates the percentage of uncommon words in the data.