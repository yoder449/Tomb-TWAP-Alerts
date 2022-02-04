# Tomb.finance Twitter Bot
# Time Weighted Average Price (TWAP) Alerts for the FTM-TOMB Peg
# Created 4 January 2022 by @yoder449

import web3
from web3 import Web3
import twitter
import requests
import pause

# @Tomb_Alerts Twitter Account Keys
api = twitter.Api(consumer_key='<sanitized>',
                  consumer_secret='<sanitized>',
                  access_token_key='<sanitized>',
                  access_token_secret='<sanitized>')

# Tomb.finance Masonry Contract Details
masonry_contract = "0x8764DE60236C5843D9faEB1B638fbCE962773B67"
masonry_url = f"https://api.ftmscan.com/api?module=contract&action=getabi&address={masonry_contract}"
masonry_req = requests.get(masonry_url)
masonry_abi = masonry_req.json()['result']

# Web3.0 Connection
w3 = Web3(web3.HTTPProvider('https://rpcapi.fantom.network'))
if w3.isConnected():
    print('Fantom Opera Network connection established.')

# Access Masonry Contract
targetContract = w3.eth.contract(address=masonry_contract, abi=masonry_abi)

# Establish current epoch state
epoch_index = targetContract.functions.epoch().call()
current_epoch = epoch_index

# Loop during every epoch
while current_epoch == epoch_index:
    print("The current epoch is " + str(current_epoch))
    print("Waiting until the next epoch begins.")
    time_to_next_epoch = targetContract.functions.nextEpochPoint().call() # provides a unix timestamp of when the next epoch will start
    pause.until(time_to_next_epoch) # using the pause.py library, pause until the next epoch begins
    print("Pausing 3 minutes to allow blockchain updates.")
    pause.minutes(3) # allow 3 minutes for smart contract updates on the blockchain
    
    # Pull the last epoch's TWAP value
    raw_twap = targetContract.functions.getTombPrice().call()
    twap_converted = round((raw_twap/1000000000000000000), 4)
    print("The last epoch's TWAP value was " + str(twap_converted))

    # Determine the next epoch's period type
    if raw_twap < 1000000000000000000:
        period_type = "contraction"
    elif twap_converted >= 1010000000000000000:
        period_type = "expansion"
    else:
        period_type = "zen"
    print("The last epoch was a period of " + period_type)

    # Post a tweet
    api.PostUpdate(
    f"Epoch {str(current_epoch)} just ended with a TWAP value of {str(twap_converted)}.\n"+
    f"Epoch {str(current_epoch+1)} begins phase of #{period_type}.\n"+
    f"https://tomb.finance/masonry \n$TOMB $TSHARE $TBOND $FTM")
    print("Tweet posted. Restarting loop.")
    
    # Re-establish loop variables for new epoch
    epoch_index = targetContract.functions.epoch().call()
    current_epoch = epoch_index
