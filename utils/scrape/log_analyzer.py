import re
import os
from collections import defaultdict
from datetime import datetime

def find_most_recent_log(log_dir):
    # Get all files in the log directory that start with "scrapy_output_" and end with ".log"
    log_files = [f for f in os.listdir(log_dir) if f.startswith('scrapy_output_') and f.endswith('.log')]

    # Sort the log files by date and time extracted from the filename (assuming format: scrapy_output_YYYYMMDD_HHMMSS.log)
    log_files.sort(reverse=True, key=lambda x: x.split('_')[2] + x.split('_')[3].split('.')[0])  # Extract date and time part
    return log_files[0] if log_files else None

def analyze_logs(log_file):
    # Regular expressions to capture errors and state information
    error_regex = re.compile(r'ERROR: (Request failed: (.+?) - .+? for state (.+))')
    success_regex = re.compile(r'Saved file .+ for state (.+)')

    # Counters and data structures
    total_links_working = 0
    total_links_not_working = 0
    state_link_status = defaultdict(lambda: {'working': 0, 'not_working': 0})
    state_link_errors = defaultdict(list)

    with open(log_file, 'r') as f:
        for line in f:
            # Check for errors
            error_match = error_regex.search(line)
            if error_match:
                total_links_not_working += 1
                error_message, link, state = error_match.groups()
                state_link_status[state]['not_working'] += 1
                state_link_errors[state].append(link)
                continue

            # Check for successful link retrievals
            success_match = success_regex.search(line)
            if success_match:
                total_links_working += 1
                state = success_match.group(1)
                state_link_status[state]['working'] += 1

    # Generate output
    output = []
    output.append(f"Total Links Working: {total_links_working}")
    output.append(f"Total Links Not Working: {total_links_not_working}")
    output.append("\nLinks by State:")
    for state, counts in state_link_status.items():
        output.append(f"State: {state}, Working: {counts['working']}, Not Working: {counts['not_working']}")

    output.append("\nDetailed List of Non-Working Links by State:")
    for state, errors in state_link_errors.items():
        output.append(f"\nState: {state}")
        for link in errors:
            output.append(f"- {link}")

    # Save the output to a text file
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"log_analysis_summary_{now}.txt"
    with open(output_file, 'w') as f:
        f.write("\n".join(output))

    print(f"Log analysis saved to {output_file}")

if __name__ == "__main__":
    log_dir = '.'  # Directory where your log files are stored
    most_recent_log = find_most_recent_log(log_dir)

    if most_recent_log:
        print(f"Analyzing log file: {most_recent_log}\n")
        analyze_logs(most_recent_log)
    else:
        print("No recent log file found.")

