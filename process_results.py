# coding: utf-8
"""Quick test script to process a results file."""
import os
import json


def main():
    """."""
    results_files = [f for f in os.listdir('.') if f.startswith('results_')]
    if results_files:
        print('Results files: (ID, Name)')
        for i, file in enumerate(results_files):
            print('{:3d} : {}'.format(i, file))
        value = input('Enter selection file ID (default={}): '.
                      format(len(results_files)-1))
        id = int(value) if value else len(results_files)-1
        print('Selected: ')
        print('   {} : {}'.format(id, results_files[id]))
        print('-' * 80)
        results = json.load(open(results_files[id]))

        # Number of results with > 100 messages
        high_counts = []
        for key in results:
            if key.startswith('total_'):
                continue
            if results[key]['count'] > 100:
                high_counts.append((key, results[key]['count']))
        high_counts = sorted(high_counts, key=lambda x: x[1], reverse=True)
        for value in high_counts:
            print('{:4d} | {}'.format(value[1], value[0][:100]))



if __name__ == '__main__':
    main()

