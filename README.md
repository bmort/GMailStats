# GMailStats
Simple Python script to gather GMail stats detailing number of messages and total message size per sender.
This can be useful for bulk cleanup of messages in gmail. 

# Installation
```bash
$ virtualenv -p python3 venv 
$ . venv/bin/activate
$ pip install -r requirements.txt
```

# Run
```bash
$ python email_stats.py
```
The first time the script is run it will open a web browser and prompt the you to authenticate the application
with your gmail account. On subsequent runs, it will use the results of this authentication and remember the associated credentials though a cache file stored at `.credentials/gmail-python-stats.json`. 

To revoke access of this application to your Google account settings https://myaccount.google.com/permissions and remove permission for 'Gmail Stats Test'. To use this script with another google account delete the credentials cache file described
above.

# Results
In addtion to reporting to stdout while running results are saved in a JSON file with the name:

`results_<datetime>.json`

where `<datatime>` is the datetime when the results were created with the format:

`%Y-%m-%d_%H:%M:%S`.

The JSON file contains a summary of all messages found in gmail organised by sender and sorted by total message size summed
over all messages from that sender in MiB. Also shown are the number of messages from the sender and the aggregated gmail
labels those messages are found in.

# Using the results
These results are particularly useful for cleaning up email in a gmail account. This can be done using the results and
search operators descibed here: https://support.google.com/mail/answer/7190?hl=en. For example using the `from:` keywork
with the sender address identified as sending a lot of unwanted messages can be used to quickly search for and bulk delete
messages quickly.

# References
For description of the Google gmail Python API see:
https://developers.google.com/gmail/api/quickstart/python
