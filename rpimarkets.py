import getpass
import time
import json
import sys
import urllib2

BASE_URL = 'http://simla.cs.rpi.edu/api/'

# Number of times to retry a trade before giving up
TRADE_RETRY_LIMIT = 6

def prompt_password():
	#user = raw_input('RPI Markets Username: ')
	#password = getpass.getpass()
	# You can hard code your username/password here if the prompt
	# is too annoying (and comment out the above two lines).
	return "danhakimi", "hakimibot"
	
def range_decision_callback(lowest_price_per_share,
                            highest_price_per_share):
		"""Return a function which decides whether to execute a trade
		based on a cost per share quote.  In this case we simply check
		that the price is in the given range, but this logic can be
		as complex as you'd like in general."""
		def decision_callback(buysell, quantity, cost_per_share):
		    decision = (lowest_price_per_share < cost_per_share
		                and cost_per_share < highest_price_per_share)
		    if decision:
		        print '%s %d shares at %1.2f per share' % (
		            buysell, quantity, cost_per_share)
		    else:
		        print ('canceled an offer to %s for %d shares at %1.2f'
		               ' per share') % (buysell, quantity, cost_per_share)
		    # Return a boolean: True to execute, False to cancel
		    return decision 
		return decision_callback

class Experiment(object):
	"""A wrapper for accessing an experiment."""

	def __init__(self, experiment, account_num, base_url=BASE_URL):
		"""Create a new Experiment object.

		experiment: The name of the experiment to access.

		account_num: The number of the account to use.  A unique number
		should be assigned to each bot you are testing simultaneously.

		base_url: The URL of the API to access."""
		self.experiment = experiment
		self.account_num = account_num
		self.base_url = base_url
		self.username = None
		self.password = None

	def poll_for_data(self, new_data_callback):
		"""Continuously call new_data_callback with new animation data
		until it returns False.  new_data_callback will be passed a list,
		which for the one-dimensional bouncing ball will be of the form:
		[(Position, Left count, Right count, Timestamp), ...]"""
		url = self.base_url + 'experiments/%s/%d/data/' % (
			self.experiment, self.account_num)
		last_timestamp = 0
		while True:
			self.authenticate()
			try:
				result = json.load(urllib2.urlopen(url))
			except urllib2.HTTPError, e:
				if e.code == 404:
					print 'No data from experiment yet'
				else:
					print 'HTTP error %d getting experiment data: %s' % (
						e.code, e.msg)
				time.sleep(2)
				continue
			new_data = []
			for point in result:
				if point[-1] > last_timestamp:
					new_data.append(point)
					last_timestamp = point[-1]
			if new_data:
				ret = new_data_callback(new_data)
				if ret is not None and not ret:
					return
			time.sleep(2)

	def trade(self, buysell, quantity, decision_callback,
		      retries=TRADE_RETRY_LIMIT):
		"""Get a price quote, then call decision_callback with that quote.
		If decision_callback returns True, then attempt to execute the
		trade. If decision_callback returns False, the trade is canceled.

		The return value is a tuple of two boolean values:
		(Trade executed, decision_callback's return)

		If there is an error getting a quote, the return will be (False,
		None)

		If we get a quote and decision_callback returns True but there is
		an error executing the trade (insufficient funds, for example),
		then the return value would be (False, True).

		If decision_callback returns True and the trade is executed, the
		return value is (True, True)

		If the price of the stock changes, we'll retry the trade up to
		TRADE_RETRY_LIMIT (default 6) times total (calling
		decision_callback with the new quote each time and acting
		accordingly).
		"""
		assert buysell in ['buy', 'sell']
		url = self.base_url + 'experiments/%s/%d/trade/%s/%d/' % (
			self.experiment, self.account_num, buysell, int(quantity))
		auth_handler = self.authenticate()
		try: 
			result = json.load(urllib2.urlopen(url))
		except Exception, e:
			time.sleep(.01)
			return self.trade(buysell, quantity, decision_callback, retries)
		if result['code'] == 0:
			decision = decision_callback(buysell, int(quantity),
				                         float(result['per_share']))
			if decision:
				try:
					opener = urllib2.build_opener(auth_handler)
					request = urllib2.Request('%s%s/' % (
							url, result['per_share']))
					request.get_method = lambda: 'POST'
					result = opener.open(request)
				except urllib2.HTTPError, e:
					reason = e.read().split('\n')
					if ('price has changed' in reason
						and retries > 1):
						print 'Price changed.  Retrying trade...'
						return self.trade(
							buysell, quantity, decision_callback,
							retries=retries-1)
					else:
						print ('HTTP error %d when trying to trade: %s '
								) % (e.code, reason)
						return (False, True)
				return (True, True)
			else:
				opener = urllib2.build_opener(auth_handler)
				request = urllib2.Request(url)
				request.get_method = lambda: 'DELETE'
				opener.open(request)
				return (False, False)
		else:
			print 'trade error: %s' % (str(result),)
			return (False, None)
				
	def tradeWrapper(self, buyOrSell, amount, low, high):
		return self.trade(buyOrSell, amount, range_decision_callback(low, high) )

	def history(self):
		"""Get the history of the stock for a given experiment.
		Returns a list of dictionary entries describing each trade."""
		try :
			url = self.base_url + 'experiments/%s/%d/history/' % (
				self.experiment, self.account_num)
			self.authenticate()
			result = json.load(urllib2.urlopen(url))
			return result
		except Exception, e :
			return self.history()

	def account(self):
		"""Get your account information: holdings and cash."""
		url = self.base_url + 'experiments/%s/%d/account/' % (
			self.experiment, self.account_num)
		self.authenticate()
		result = json.load(urllib2.urlopen(url))
		return result

	def authenticate(self):
		"""Prompt once for a username/password, but otherwise make sure
		credentials are refreshed to avoid authorization errors.  Using
		basic HTTP authentication."""
		if self.username is None or self.password is None:
			self.username, self.password = prompt_password()
		password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
		password_mgr.add_password(None, uri=self.base_url,
									user=self.username,
									passwd=self.password)
		auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(auth_handler)
		urllib2.install_opener(opener)
		return auth_handler
