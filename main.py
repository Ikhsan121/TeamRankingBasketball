import asyncio
from playwright.async_api import async_playwright
import csv
import os
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import re


async def match_page(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=20000)

        # initialize team's list
        team1, team2 = [], []
        atsstrike1, atsstrike2 = [], []
        team1_name_list, team2_name_list = [], []

        # using bs4 to get all fields
        page_content = await page.content()
        soup = BeautifulSoup(page_content, 'html.parser')
        # get date played
        date_string = soup.find('p', class_='h1-sub space-top-none').text.split("-")[0].strip()
        month = date_string.split()[1]
        day_num = date_string.split()[2].replace(",", "")
        year = date_string.split()[3]
        formatted_date_string = f"{month} {day_num}, {year}"
        parsed_date = datetime.strptime(formatted_date_string, '%b %d, %Y')
        formatted_date = parsed_date.strftime('%m/%d/%Y')
        team1.append(formatted_date)
        team2.append(formatted_date)

        # get home, away, or neutral and team's name
        h1 = soup.find('h1', id='h1-title').text
        if "vs." in h1.split():
            team1.append("Neutral")
            team2.append("Neutral")
            # team's name
            team1_name = h1.split('vs.')[0].strip()
            team2_name = h1.split('vs.')[1].strip().split(":")[0]
            team1.append(team1_name)
            team2.append(team2_name)
            team1_name_list.append(team1_name)
            team2_name_list.append(team2_name)
        else:
            team1.append("Away")
            team2.append("Home")
            # team's name
            team1_name = h1.split(' at ')[0].strip()
            team2_name = h1.split(' at ')[1].strip().split(":")[0]
            team1.append(team1_name)
            team2.append(team2_name)
            team1_name_list.append(team1_name)
            team2_name_list.append(team2_name)

        # Get rank for each team
        rank = await get_rank(date=formatted_date.split('/'))
        team1_rank = rank[0]
        team2_rank = rank[1]
        # add ranking to each team1
        for i in team1_rank:
            for j in team1_name_list:
                if i == j:
                    team1.append(team1_rank[i])
        # add ranking to each team2
        for i in team2_rank:
            for j in team2_name_list:
                if i == j:
                    team2.append(team2_rank[i])

        # input spread and total
        try:
            spread = soup.find('p', class_='h1-sub space-top-none').text.split("Odds:")[1].strip().split("by")[1].split(
                ",")[0].strip()
            spread_title = soup.find('table', class_='tr-table matchup-table').find('tbody').find('tr').find(
                'td').text.strip()
            total = soup.find('p', class_='h1-sub space-top-none').text.split("Odds:")[1].strip().split(' ')[-1]
            # check the Odds for
            if spread_title == team2_name:
                team1.append("")
                team2.append(f"-{spread}")
                team1.append(total)
                team2.append("")
            elif spread_title == team1_name:
                team1.append("")
                team2.append(spread)
                team1.append(total)
                team2.append("")
        except:
            team1.append("")
            team2.append("N/A")
            team1.append("N/A")
            team2.append("")

        # point_analysis, over_under_analysis, matchups_stats
        cookies = page.locator('button#onetrust-accept-btn-handler')
        await cookies.click()
        await page.get_by_role('link', name='Picks & Odds ').click()
        point_analysis = await page.get_by_role('link', name='Point Spread Analysis').get_attribute('href')
        over_under_analysis = await page.get_by_role('link', name='Over/Under Analysis').get_attribute('href')
        await page.get_by_role('link', name='Ratings & Stats ').click()
        matchups_stats = await page.get_by_role('link', name='Matchup Stats').get_attribute('href')

        # Go to ATS page in new browser page
        ats_page = await browser.new_page()
        await ats_page.goto('https://www.teamrankings.com' + point_analysis)
        ats_page_content = await ats_page.content()

        # Get ATS and ATS %
        soup = BeautifulSoup(ats_page_content, 'html.parser')
        ats_table = soup.find_all('table', class_='tr-table scrollable')[1]
        ats_season = ats_table.find_all('tr')[1]
        ats_season_team1 = ats_season.find_all('td')[1].text.split("-")
        ats_season_team2 = ats_season.find_all('td')[3].text.split("-")

        # add ats W to team 1
        team1.append(str(ats_season_team1[0]))
        # add ats L to team 1
        team1.append(str(ats_season_team1[1]))
        # add ats percentage to team 1
        ats1 = int(ats_season_team1[0])*100/(int(ats_season_team1[0]) + int(ats_season_team1[1]))
        team1.append(f"{ats1:.0f}%")
        # add ats W to team 2
        team2.append(str(ats_season_team2[0]))
        # add ats L to team 2
        team2.append(str(ats_season_team2[1]))
        # add ats percentage to team 1
        ats2 = int(ats_season_team2[0])*100/(int(ats_season_team2[0]) + int(ats_season_team2[1]))
        team2.append(f"{ats2:.0f}%")

        # Get ATS strike
        ats_table1 = soup.find('table', id='DataTables_Table_0')
        ats_table2 = soup.find('table', id='DataTables_Table_1')
        ats_rows1 = ats_table1.find('tbody').find_all('tr')
        ats_rows2 = ats_table2.find('tbody').find_all('tr')

        # ATS strikes for team 1
        for row in ats_rows1:
            total_column = row.find_all('td')[3].text.strip()
            if total_column != "--":
                result_column1 = list(row.find_all('td')[5].text.strip())[0]
                atsstrike1.append(result_column1)
        atsstrike1.reverse()
        win_strike1 = 0
        lose_strike1 = 0
        play_strike1 = 0
        first_item = atsstrike1[0]
        # item for ATS strike column
        if first_item == "+":
            for i in range(len(atsstrike1)):
                if first_item == atsstrike1[i]:
                    win_strike1 += 1
                else:
                    break
        if first_item == "-":
            for i in range(len(atsstrike1)):
                if first_item == atsstrike1[i]:
                    lose_strike1 += 1
                else:
                    break
        if first_item == "0":
            for i in range(len(atsstrike1)):
                if first_item == atsstrike1[i]:
                    play_strike1 += 1
                else:
                    break

        # ats strike for team 2
        for row in ats_rows2:
            total_column = row.find_all('td')[3].text.strip()
            if total_column != "--":
                result_column2 = list(row.find_all('td')[5].text.strip())[0]
                atsstrike2.append(result_column2)
        atsstrike2.reverse()
        win_strike2 = 0
        lose_strike2 = 0
        play_strike2 = 0
        first_item = atsstrike2[0]
        if first_item == "+":
            for i in range(len(atsstrike2)):
                if first_item == atsstrike2[i]:
                    win_strike2 += 1
                else:
                    break
        if first_item == "-":
            for i in range(len(atsstrike2)):
                if first_item == atsstrike2[i]:
                    lose_strike2 += 1
                else:
                    break
        if first_item == "0":
            for i in range(len(atsstrike2)):
                if first_item == atsstrike2[i]:
                    play_strike2 += 1
                else:
                    break

        # Get OU and OU%
        ou_page = await browser.new_page()
        await ou_page.goto('https://www.teamrankings.com' + over_under_analysis)
        uo_page_content = await ou_page.content()
        soup = BeautifulSoup(uo_page_content, 'html.parser')
        uo_table = soup.find_all('table', class_='tr-table scrollable')[1]
        uo_season = uo_table.find_all('tr')[1]
        uo_season_team1 = uo_season.find_all('td')[1].text.split("-")
        uo_season_team2 = uo_season.find_all('td')[2].text.split("-")
        # add O to team 1
        team1.append(str(uo_season_team1[0]))
        # add U to team 1
        team1.append(str(uo_season_team1[1]))
        # add uo percentage to team 1
        uo1 = int(uo_season_team1[0]) * 100 / (int(uo_season_team1[0]) + int(uo_season_team1[1]))
        team1.append(f"{uo1:.0f}%")
        # add O to team 2
        team2.append(str(uo_season_team2[0]))
        # add U to team 2
        team2.append(str(uo_season_team2[1]))
        # add uo percentage to team 1
        uo2 = int(uo_season_team2[0]) * 100 / (int(uo_season_team2[0]) + int(uo_season_team2[1]))
        team2.append(f"{uo2:.0f}%")

        # use bs4 to scrape Matchup Stats
        p = requests.get('https://www.teamrankings.com' + matchups_stats)
        soup = BeautifulSoup(p.text, 'html.parser')
        table1 = soup.find_all('table', class_='tr-table scrollable')[2]
        table2 = soup.find_all('table', class_='tr-table scrollable')[3]
        two_point_percentage_Off_team1 = table1.find_all('tr')[5].find_all('td')[1].text.split('%')[0]
        two_point_percentage_Def_team1 = table2.find_all('tr')[5].find_all('td')[2].text.split('%')[0]
        three_point_percentage_Off_team1 = table1.find_all('tr')[4].find_all('td')[1].text.split('%')[0]
        three_point_percentage_Def_team1 = table2.find_all('tr')[4].find_all('td')[2].text.split('%')[0]
        free_throw_percentage_Off_team1 = table1.find_all('tr')[3].find_all('td')[1].text.split('%')[0]
        free_throw_percentage_Def_team1 = table2.find_all('tr')[3].find_all('td')[2].text.split('%')[0]
        team1.extend([
            two_point_percentage_Off_team1,
            two_point_percentage_Def_team1,
            three_point_percentage_Off_team1,
            three_point_percentage_Def_team1,
            free_throw_percentage_Off_team1,
            free_throw_percentage_Def_team1,
        ])

        two_point_percentage_Off_team2 = table2.find_all('tr')[5].find_all('td')[1].text.split('%')[0]
        two_point_percentage_Def_team2 = table1.find_all('tr')[5].find_all('td')[2].text.split('%')[0]
        three_point_percentage_Off_team2 = table2.find_all('tr')[4].find_all('td')[1].text.split('%')[0]
        three_point_percentage_Def_team2 = table1.find_all('tr')[4].find_all('td')[2].text.split('%')[0]
        free_throw_percentage_Off_team2 = table2.find_all('tr')[3].find_all('td')[1].text.split('%')[0]
        free_throw_percentage_Def_team2 = table1.find_all('tr')[3].find_all('td')[2].text.split('%')[0]
        team2.extend([
            two_point_percentage_Off_team2,
            two_point_percentage_Def_team2,
            three_point_percentage_Off_team2,
            three_point_percentage_Def_team2,
            free_throw_percentage_Off_team2,
            free_throw_percentage_Def_team2,
        ])

        # add item for ATS strike team 1
        if atsstrike1[0] == "+":
            team1.append(f"{win_strike1}")
        elif atsstrike1[0] == "-":
            team1.append(f"-{lose_strike1}")
        else:
            team1.append("0")

        # add item for ATS strike team 2
        if atsstrike2[0] == "+":
            team2.append(f"{win_strike2}")
        elif atsstrike2[0] == "-":
            team2.append(f"-{lose_strike2}")
        else:
            team2.append(f"0")

        # OU strikes
        soup = BeautifulSoup(uo_page_content, 'html.parser')
        uo_table1 = soup.find('table', id='DataTables_Table_0')
        uo_table1_rows = uo_table1.find('tbody').find_all('tr')
        uo_table2 = soup.find('table', id='DataTables_Table_1')
        uo_table2_rows = uo_table2.find('tbody').find_all('tr')
        uostrk2 = []
        uostrk1 = []
        for row in uo_table1_rows:
            total_column = row.find_all('td')[3].text.strip()
            if total_column != "--":
                result_column1 = row.find_all('td')[5].text.strip()
                uostrk1.append(result_column1)
        # OU strikes team 1
        uostrk1.reverse()
        under1 = 0
        over1 = 0
        push1 = 0
        first_item = uostrk1[0]
        if first_item == "Under":
            for i in range(len(uostrk1)):
                if first_item == uostrk1[i]:
                    under1 += 1
                else:
                    break
        if first_item == "Over":
            for i in range(len(uostrk1)):
                if first_item == uostrk1[i]:
                    over1 += 1
                else:
                    break
        if first_item == "Push":
            for i in range(len(uostrk1)):
                if first_item == uostrk1[i]:
                    push1 += 1
                else:
                    break
        # add item for OU strikes team 1
        if over1 != 0:
            team1.append(f"{over1}")
        elif under1 != 0:
            team1.append(f"-{under1}")
        elif push1 != 0:
            team1.append(f"0")
        # OU strikes for team2
        for row in uo_table2_rows:
            total_column = row.find_all('td')[3].text.strip()
            if total_column != "--":
                result_column2 = row.find_all('td')[5].text.strip()
                uostrk2.append(result_column2)
        uostrk2.reverse()
        under2 = 0
        over2 = 0
        push2 = 0
        first_item = uostrk2[0]
        if first_item == "Under":
            for i in range(len(uostrk2)):
                if first_item == uostrk2[i]:
                    under2 += 1
                else:
                    break
        if first_item == "Over":
            for i in range(len(uostrk2)):
                if first_item == uostrk2[i]:
                    over2 += 1
                else:
                    break
        if first_item == "Push":
            for i in range(len(uostrk2)):
                if first_item == uostrk2[i]:
                    push2 += 1
                else:
                    break
        # add item for OU strikes team 2
        if over2 != 0:
            team2.append(f"{over2}")
        elif under2 != 0:
            team2.append(f"-{under2}")
        elif push2 != 0:
            team2.append(f"0")

        # ATS l6 W and ATS l6 L
        if len(atsstrike1) >= 6:
            team1.append(int(atsstrike1[:6].count('+')))
            team1.append(int(atsstrike1[:6].count('-')))
        else:
            team1.append(int(atsstrike1[:len(atsstrike1)].count('+')))
            team1.append(int(atsstrike1[:len(atsstrike1)].count('-')))
        if len(atsstrike2) >= 6:
            team2.append(int(atsstrike2[:6].count('+')))
            team2.append(int(atsstrike2[:6].count('-')))
        else:
            team2.append(int(atsstrike2[:len(atsstrike2)].count('+')))
            team2.append(int(atsstrike2[:len(atsstrike2)].count('-')))

        # O and U l6 for team 1
        under1_l6 = 0
        over1_l6 = 0
        if len(uostrk1) >= 6:
            for i in range(6):
                if "Under" == uostrk1[i]:
                    under1_l6 += 1
                elif "Over" == uostrk1[i]:
                    over1_l6 += 1
        else:
            for i in range(len(uostrk1)):
                if "Under" == uostrk1[i]:
                    under1_l6 += 1
                elif "Over" == uostrk1[i]:
                    over1_l6 += 1
        # O and U l6 for team 2
        under2_l6 = 0
        over2_l6 = 0
        if len(uostrk2) >= 6:
            for i in range(6):
                if "Under" == uostrk2[i]:
                    under2_l6 += 1
                elif "Over" == uostrk2[i]:
                    over2_l6 += 1
        else:
            for i in range(len(uostrk2)):
                if "Under" == uostrk2[i]:
                    under2_l6 += 1
                elif "Over" == uostrk2[i]:
                    over2_l6 += 1
        # ou l6
        team1.append(over1_l6)
        team1.append(under1_l6)
        team2.append(over2_l6)
        team2.append(under2_l6)
        data = {
            'team1': team1,
            'team2': team2
        }
        await browser.close()
        print(f"{url.split('/')[-1]}: Success")
    return data
async def get_rank(date):
    team1 = []
    team2 = []
    team1_name = []
    team2_name = []
    result = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        date_url = f"{date[2]}-{date[0]}-{date[1]}"
        url = f"https://www.teamrankings.com/ncb/schedules/?date={date_url}"
        await page.goto(url, timeout=20000)
        page_content = await page.content()
        soup = BeautifulSoup(page_content, 'html.parser')
        table = soup.find('table', id='DataTables_Table_0')
        rows = table.find_all('a')
        for row in rows:
            # list of rank
            rank = [x.replace("#", "") for x in row.text.split() if "#" in x]
            # team's name
            if " at " in row.text:
                original_list = row.text.replace("#", "").split(" at ")
                result_list = [re.sub(r'\d', '', s).strip() for s in original_list]
                team1_name.append(result_list[0])
                team2_name.append(result_list[1])
            elif 'vs.' in row.text:
                original_list = row.text.replace("#", "").split("vs.")
                result_list = [re.sub(r'\d', '', s).strip() for s in original_list]
                team1_name.append(result_list[0])
                team2_name.append(result_list[1])
            team1.append(rank[0])
            team2.append(rank[1])

        # create a dictionary where the key is team's name and tha value is the team's rank
        team1_dict = dict(zip(team1_name, team1))
        team2_dict = dict(zip(team2_name, team2))
        result.append(team1_dict)
        result.append(team2_dict)
        await browser.close()
    return result
async def user_prompt():
    links = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # go to over under page
        page = await browser.new_page()
        await page.goto("https://www.teamrankings.com/ncb/schedules/season/")
        table = await page.query_selector("table#DataTables_Table_0")
        theads = await table.query_selector_all('thead')
        tbodies = await table.query_selector_all('tbody')
        theads_list = []
        for head in theads:
            inner_text = await head.inner_text()
            split_text = inner_text.split()
            theads_list.append(split_text[1] + " " + split_text[2])

        # Store all matchups games in one day into a list
        tbodies_list = []
        for tbody in tbodies:
            tbodies_list.append(tbody)

        # Create a dictionary from the two lists
        my_dict = dict(zip(theads_list, tbodies_list))
        # create key value pairs of index and date {1: 'Nov6'}
        match_dates_list = list(my_dict.keys())
        match_dates_dict = dict(zip([x+1 for x in range(len(match_dates_list))], match_dates_list))
        # ask user to input a particular date or a range of date options
        options = input("Type 1 to select one match.\nType 2 to select multiple matches.\n")
        if options == "1":
            for i in range(len(match_dates_list)):
                print(f"{i+1}. {match_dates_list[i]}")
            match_date = int(input("Input the index of the match date: "))
            # looping
            for i in match_dates_dict:
                if match_date == i:
                    rows = await list(my_dict.values())[i-1].query_selector_all('a')
                    for row in rows:
                        links.append("https://www.teamrankings.com" + await row.get_attribute('href'))
            user = {
                'date': match_dates_dict[match_date],
                'links': links
            }
        elif options == "2":
            for i in range(len(match_dates_list)):
                print(f"{i+1}. {match_dates_list[i]}")
            match_date = input("Input the range of index of the match date [a-b]: ")
            initial_date = int(match_date.split("-")[0])
            final_date = int(match_date.split("-")[1])
            date_range = [x for x in range(initial_date, final_date+1)]
            for i in match_dates_dict:
                if i in date_range:
                    rows = await list(my_dict.values())[i - 1].query_selector_all('a')
                    for row in rows:
                        links.append("https://www.teamrankings.com" + await row.get_attribute('href'))
            user = {
                'date': f'{match_dates_dict[initial_date]}-{match_dates_dict[final_date]}',
                'links': links
            }
        await browser.close()
    return user
def create_excel(csv_file_path, final_data):
    # Open the CSV file in write mode
    try:
        with open(csv_file_path, 'w', newline='') as csv_file:
            # Create a CSV writer
            csv_writer = csv.writer(csv_file)
            # Write each list in the main list as a separate row in the CSV file
            csv_writer.writerows(final_data)
        df = pd.read_csv(csv_file_path)
        df.insert(0, 'Game#', [i // 2 + 1 for i in range(len(df))])
        df.to_excel(f'{csv_file_path.split(".")[0]}.xlsx', index=False)
        # delete csv file
        # Check if the file exists before attempting to delete it
        if os.path.exists(csv_file_path):
            # Delete the file
            os.remove(csv_file_path)
    except ModuleNotFoundError:
        input("Press Enter to exit...")
async def main():
    columns_title = ['Date', 'H/A/Neutral', 'Teams', "TN Rank", 'Spread', 'Total', 'ATS W', 'ATS L', 'ATS%', 'O', 'U',
                     'OU%', '2p%O', '2p%D', '3p%O', '3p%D', 'FT%O',
                     'FT%D', 'ATSStrk', 'OUStrk', 'ATS L6 W', 'ATS L6 L', "O L6", 'U L6']
    final_data = [columns_title]

    # User prompt
    user = await user_prompt()
    links = user['links']
    for link in links:
        result = await match_page(link)
        final_data.append(result['team1'])
        final_data.append(result['team2'])
        # # create excel
        create_excel(csv_file_path=f"{user['date']}.csv", final_data=final_data)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ModuleNotFoundError:
        # Wait for user input before exiting
        input("Press Enter to exit...")

