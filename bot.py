from rpimarkets import Experiment

EXPERIMENT_NAME = 'b6'
ACCOUNT_NUM = 0
balldata = [] #global history
exp = Experiment(EXPERIMENT_NAME, ACCOUNT_NUM)
	
def historicBuys ( recentHistory ):
	count = 0
	l = len(recentHistory)
	buys = 0
	
	while ( count+1 < l ):
		if ( recentHistory[count+1]['price'] > recentHistory[count]['price'] ):
			buys = buys + 1
		
		count = count + 1
	
	return buys


def findRoughExpectedValue():
	history = exp.history()
	if len(history) > 0:
		currentPrice = history[-1]['price']
	else:
		currentPrice = 50
	
	total_left = balldata[-1]["left"]
	total_right = balldata[-1]["right"]
	
	print total_left
	print total_right
	
	total_move = ( 1.0 * total_left / (total_left + total_right) * 100.0 )
	
	recent_left = total_left - balldata[ -int( len(balldata)**.5 )]["left"]
	recent_right = total_right - balldata[ -int( len(balldata)**.5 )]["right"]
	
	if recent_left + recent_right == 0 :
		recent_left = currentPrice
		recent_right = 100-currentPrice
		
	recent_move = (recent_left / (recent_left + recent_right) * 100)
	
	h2 = int( len(history)**.5 )
	if h2 > 0 :
		recent_change = historicBuys(history[-h2:]) * 100 / h2 * currentPrice / 50
	else :
		recent_change = 2 * currentPrice

	print currentPrice
	print total_move
	print recent_move
	print recent_change
	ev = (	.55 * currentPrice + 
			.14 * total_move +
			.17 * recent_move +
			.14 * recent_change )

	return ev

def listener (new_data):
    """When registered with rpimarkets.poll_for_data, prints out a
    console version of the bouncing ball animation.  This function
    could return False to stop polling for data."""
    for position, left, right, timestamp in new_data:
    	balldata.append({"position" : position, "left" : left,
    						"right" : right, "t" : timestamp })
    						
	print "Got data!"
	#Deal With new_data, balldata
	
	total_left = balldata[-1]["left"]
	total_right = balldata[-1]["right"]
	
	if (total_left + total_right >= 2):
		#to find expected value
		expectedValue = findRoughExpectedValue()
		print expectedValue
		#to trade:
		count = 0
		while ( ( count < 4 ) and ( exp.tradeWrapper('buy', 4-count, 0, expectedValue-2) == (True, True) ) ):
			count = count + 1
		count = 0
		while ( (count < 4) and ( exp.tradeWrapper('sell', 4-count, expectedValue+2, 100) == (True, True) ) ):
			count = count + 1
	

def main():
    # Place a sell order for 1 share if the stock's value
    # is between 75 and 100
    # Print information about the last two stock trades
    #	print exp.history()
    
    # Print information about your account
    #	print exp.account()
    # Start polling for bouncing ball data
    exp.poll_for_data( listener )
    	
    
if __name__ == '__main__':
	main()

