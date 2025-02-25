from playwright.async_api import async_playwright


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

if __name__ == '__main__':
    print("user_prompt is running")

