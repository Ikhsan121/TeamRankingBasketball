import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


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
