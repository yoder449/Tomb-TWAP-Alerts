# Tomb.finance Twitter Bot
# Time Weighted Average Price (TWAP) Alerts for the FTM-TOMB Peg
# Created by @yoder449, special thanks to @notjebb#9487 for their assistance!
# Revision History:
# 4 January 2022: Baseline
# 6 March 2022: Added exception handling for RPC request issues

import web3
from web3 import Web3
import twitter
import requests
import pause

# @Tomb_Alerts Twitter Account Keys
api = twitter.Api(consumer_key='',
                  consumer_secret='',
                  access_token_key='',
                  access_token_secret='')

# Tomb.finance Masonry Contract Details
masonry_contract = "0x8764DE60236C5843D9faEB1B638fbCE962773B67"
masonry_url = f"https://api.ftmscan.com/api?module=contract&action=getabi&address={masonry_contract}"
masonry_req = requests.get(masonry_url)
masonry_abi = masonry_req.json()['result']

# Web3.0 Connection
w3 = Web3(web3.HTTPProvider('https://rpcapi.fantom.network'))
if w3.isConnected():
    print('TWAP_Alerts.py: Fantom Opera Network connection established.')

# Access Masonry Contract
targetContract = w3.eth.contract(address=masonry_contract, abi=masonry_abi)

# Establish baseline epoch state
epoch_index = targetContract.functions.epoch().call()
current_epoch = epoch_index
pause.seconds(5) # avoid too many RPC requests...
prev_raw_twap = targetContract.functions.getTombPrice().call()
if prev_raw_twap < 1000000000000000000:
    prev_period_type = "contraction"
elif prev_raw_twap >= 1010000000000000000:
    prev_period_type = "expansion"
else:
    prev_period_type = "zen"
print(f"TWAP_Alerts.py: Epoch {str(epoch_index)} baseline was a period of {prev_period_type}.")

# Loop during every epoch
while current_epoch == epoch_index:
    print(f"TWAP_Alerts.py: The current epoch is {str(current_epoch)}.")
    print("TWAP_Alerts.py: Waiting until the next epoch begins.")
    for x in range (0, 5):
        try:
            time_to_next_epoch = targetContract.functions.nextEpochPoint().call() # provides a unix timestamp of when the next epoch will start
            pause.until(time_to_next_epoch) # using the pause.py library, pause until the next epoch begins
            print("TWAP_Alerts.py: Pausing 3 minutes to allow blockchain updates.")
            pause.minutes(3) # allow 3 minutes for smart contract updates on the blockchain
            RPC_error = None
        except Exception as RPC_error:
            pass
        if RPC_error:
            print(f"TWAP_Alerts.py: nextEpochPoint exception occurred. (Error {x} of 5.")
            pause.minutes(5)
        else:
            break

    # Pull the last epoch's TWAP value
    for x in range (0, 5):
        try:
            curnt_raw_twap = targetContract.functions.getTombPrice().call()
            pause.seconds(5) # avoid too many RPC requests...
            curnt_twap_converted = round((curnt_raw_twap/1000000000000000000), 4)
            print("TWAP_Alerts.py: The last epoch's TWAP value was " + str(curnt_twap_converted) + ".")
            RPC_error = None
        except Exception as RPC_error:
            pass
        if RPC_error:
            print(f"TWAP_Alerts.py: getTombPrice exception occurred. (Error #{x} of 5.)")
            pause.minutes(5)
        else:
            break

    # Determine the next epoch's period type
    if curnt_raw_twap < 1000000000000000000:
        curnt_period_type = "contraction"
    elif curnt_raw_twap >= 1010000000000000000:
        curnt_period_type = "expansion"
    else:
        curnt_period_type = "zen"
    print(f"TWAP_Alerts.py: The last epoch was a period of {curnt_period_type}.")
    print(f"TWAP_ALERTS.py: The prior epoch was a period of {prev_period_type}.")

    # Post a tweet for a continuation of Masonry status
    if curnt_period_type == prev_period_type:
        api.PostUpdate(
        f"[End of Epoch {str(current_epoch)}]\n\n"+
        f"TWAP: {str(curnt_twap_converted)}\n"+
        f"Continuing #{curnt_period_type} phase.\n\n"+
        f"$TOMB $TSHARE $TBOND $FTM")
        print("TWAP_Alerts.py: Continuation tweet posted. Restarting loop.")
    # Post a tweet that states "beginning new phase"
    else:
        api.PostUpdate(
        f"[End of Epoch {str(current_epoch)}]\n\n"+
        f"TWAP: {str(curnt_twap_converted)}\n"+
        f"Beginning #{curnt_period_type} phase.\n\n"+
        f"$TOMB $TSHARE $TBOND $FTM")
        print("TWAP_Alerts.py: New phase tweet posted. Restarting loop.")
    
    # Re-establish loop variables for the new epoch
    prev_period_type = curnt_period_type
    for x in range (0,5):
        try:
            epoch_index = targetContract.functions.epoch().call()
            pause.seconds(5)
            RPC_error = None
        except Exception as RPC_error:
            pass
        if RPC_error:
            print(f"TWAP_Alerts.py: Epoch call exception. (Error {x} of 5.)")
            pause.minutes(5)
        else:
            break
    current_epoch = epoch_index