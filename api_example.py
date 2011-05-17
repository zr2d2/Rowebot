from rpimarkets import Experiment

EXPERIMENT_NAME = 'test'

# Account number to use.  Changing this will give you new cash,
# new holdings, and different data.  Useful for testing multiple
# bots.
ACCOUNT_NUM = 0

balldata = [] #global history

def example():
    exp = Experiment(EXPERIMENT_NAME, ACCOUNT_NUM)
    # Place a sell order for 1 share if the stock's value
    # is between 75 and 100
    #exp.tradeWrapper('sell', 1, 49, 51)
    # Print information about the last two stock trades
    #print exp.history()[-2:]
    # Print information about your account
    print exp.account()
    # Start polling for bouncing ball data
    #exp.poll_for_data(poll_example_callback)

def poll_example_callback(new_data):
    """When registered with rpimarkets.poll_for_data, prints out a
    console version of the bouncing ball animation.  This function
    could return False to stop polling for data."""
    for position, left, right, timestamp in new_data:
    	balldata.append({"position" : position, "left" : left,
    						"right " : right, "t" : timestamp })
    
	print balldata[-1]["left"]

def main():
    # Run several API examples.  You should call your own function here.
    example()
    
if __name__ == '__main__':
    main()
