# coding=utf-8
# pylint: disable=no-member
"""Get GMail email stats."""
import argparse
import datetime
import json
import os
import time
from pprint import pprint

import httplib2
from apiclient import discovery
from googleapiclient.http import BatchHttpRequest
from oauth2client import client, tools
from oauth2client.file import Storage

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail Stats Test'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow in completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-python-stats.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials


def list_labels():
    """List Gmail labels."""
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        print('-' * 79)
        for label in labels:
            print('{:40s} {:40s} {:40s}'
                  .format(label['id'], label['name'], label['type']))
        print('-' * 79)


class GMailStats:  # pylint: disable-msg=R0903
    """Class to obtain useful GMail stats."""

    def __init__(self):
        credentials = get_credentials()
        self._http = credentials.authorize(httplib2.Http())
        self._service = discovery.build('gmail', 'v1', http=self._http)
        self._stats = dict()
        self._messages = self._service.users().messages()
        self._total_messages = 0
        self._labels = dict()
        self.get_labels()

    def get_labels(self):
        """."""
        results = self._service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        if not labels:
            print('No labels found.')
        else:
            for label in labels:
                self._labels[label['id']] = label['name']

    @staticmethod
    def _results_filename():
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        filename = 'results_%s.json' % now
        while os.path.exists(filename):
            time.sleep(1)
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            filename = 'results_%s.json' % now
        return filename

    def run(self):
        """."""
        filename = self._results_filename()
        print('- Saving results with filename: %s' % filename)
        self._stats = dict()
        start_time = time.time()
        request, response = None, None
        block_id = 0
        # labelIds = 'INBOX'
        label_ids = None
        while True:
            block_start_time = time.time()
            # Get (next) block of message Ids
            if not request:
                request = self._messages.list(userId='me',
                                              maxResults=None,
                                              includeSpamTrash=False,
                                              labelIds=label_ids)
            else:
                request = self._messages.list_next(previous_request=request,
                                                   previous_response=response)
            if not request:
                break
            response = request.execute()
            # Get headers for messages in the message block
            batch = BatchHttpRequest()
            if not response['messages']:
                break
            for message in response['messages']:
                message_id = message['id']
                message_request = self._messages.get(userId='me',
                                                     id=message_id,
                                                     format='metadata',
                                                     metadataHeaders='From')
                if message_request:
                    batch.add(request=message_request,
                              callback=self._process_messages)
            # Evaluate message stats for the block.
            batch.execute(http=self._http)
            self._total_messages += len(response['messages'])
            print('[%04i] Elapsed (s) = %-7.2f (+%.2f) [messages = %i]'
                  % (block_id, time.time() - start_time,
                     time.time() - block_start_time, self._total_messages))
            block_id += 1
            # Save and print stats
            self._save_stats(filename)

    def _save_stats(self, filename):
        """."""
        # Sort by size.
        keys = sorted(self._stats,
                      key=lambda x: self._stats[x]['size'],
                      reverse=True)
        total_size = 0
        for key in self._stats:
            total_size += self._stats[key]['size']
        sorted_dict = dict()
        sorted_dict['total_messages'] = self._total_messages
        sorted_dict['total_senders'] = len(self._stats)
        sorted_dict['total_size'] = ('%.2f MiB' % total_size)
        for key in keys:
            sorted_dict[key] = self._stats[key]
        # Print the results
        print('Top 20 results:')
        print('-' * 80)
        for i, key in enumerate(sorted_dict.keys()):
            if not key.startswith('total_'):
                print('%50s | %4i | %7.2f MiB' % (key[:50],
                                                  sorted_dict[key]['count'],
                                                  sorted_dict[key]['size']))
            else:
                print('%s = %s' % (key, sorted_dict[key]))
            if i > 10:
                break
        print('-' * 80)
        with open('{}'.format(filename), 'w') as file:
            json.dump(sorted_dict, file, indent=2)

    # pylint: disable-msg=W0613
    def _process_messages(self, request_id, response, exception):
        """Process a set of messages."""
        # pprint(request_id)
        if exception is not None:
            # Do something with the exception.
            pass
        else:
            # pprint(response)
            if 'payload' not in response:
                print('Warning: No payload...')
                pprint(response)
                return
            if 'headers' not in response['payload']:
                print('Warning: No headers...')
                pprint(response)
                return
            if len(response['payload']['headers']) > 1:
                print('Warning: header length > 1')
                pprint(response)
                return

            size = response['sizeEstimate'] / 1024**2
            labels = []
            if 'labelIds' in response:
                labels = response['labelIds']
                for i, label in enumerate(labels):
                    labels[i] = self._labels[label]
            sender = response['payload']['headers'][0]['value']

            if sender in self._stats:
                self._stats[sender]['count'] += 1
                self._stats[sender]['size'] += size
                for label in labels:
                    if label not in self._stats[sender]['labels']:
                        self._stats[sender]['labels'].append(label)
            else:
                self._stats[sender] = {
                    'count': 1,
                    'size': size,
                    'labels': labels
                }


def main():
    """Shows basic usage of Gmail API.

    Creates a GMail API service object and outputs a list of label names of the
    users's GMail account.
    """
    # list_labels()
    stats = GMailStats()
    stats.run()


if __name__ == '__main__':
    main()
