# Web Scraping & Data Processing Project

## Overview
This project automates the process of web scraping for extracting match data, analyzing team rankings, and exporting the results into an Excel file. It uses **Playwright**, **BeautifulSoup**, and **Pandas** to gather, process, and structure the data.

## Features
- Scrapes match data and rankings from `teamrankings.com`
- Extracts detailed game statistics
- Saves the collected data into an Excel file
- Supports multiple match selections via a user prompt

## Requirements
Before running the scripts, install the necessary dependencies:

```sh
pip install pandas playwright beautifulsoup4 requests
playwright install
```

## Files and Their Purpose
### `main.py`
- The main execution script.
- Calls `user_prompt.py` to get user input for match selection.
- Calls `scraping_process.py` to scrape data for selected matches.
- Saves the collected data into an Excel file.

### `user_prompt.py`
- Asks the user to select match dates.
- Retrieves match URLs based on user selection.

### `scraping_process.py`
- Extracts match details using Playwright and BeautifulSoup.
- Retrieves date, team names, rankings, spread, total, and statistical data.

### `get_rank.py`
- Fetches team rankings based on match dates.
- Uses BeautifulSoup to parse ranking data.

### `create_excel.py`
- Converts the scraped data into a structured CSV file.
- Enhances the file by adding match numbers.
- Converts the CSV file into an Excel file.

## How to Run
1. Run the main script:
   ```sh
   python main.py
   ```
2. Follow the on-screen prompts to select match dates.
3. The script will scrape data and save results into an Excel file.

## Notes
- Ensure Playwright is properly installed before running the scripts.
- The script will delete the intermediate CSV file after creating the final Excel file.

## License
This project is licensed under the MIT License.
