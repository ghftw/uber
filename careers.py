from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup as bs
import re
import traceback
import csv


def strip_html(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data).replace('in ', '')


# REQUIRED: https://github.com/mozilla/geckodriver/releases
driver_path = 'C:/webdrivers/geckodriver.exe'

# VARIABLES
options = Options()
options.add_argument("-headless")
url = "https://www.uber.com/us/en/careers/list/"


with (webdriver.Firefox(options=options) as driver):
    link = None
    driver.set_page_load_timeout(10)
    try:

        driver.get(url)
        driver.maximize_window()
        time.sleep(2)

        # CLICK COOKIES
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '/html/body/div[4]/div/div/div/div[2]/button[2]'))).click()
        time.sleep(2)

        # CLICK SURVEY
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '/html/body/div[3]/div[2]/div[1]/div[1]/a'))).click()
        time.sleep(1)

        # COLLECT JOB TOTAL
        total_p = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 '/html/body/div[1]/div/div/div[1]/main/div[2]/div/div/div/div/div[3]/div/div[2]/div/div/p'))).text
        total_jobs = int(total_p.split(' open roles')[0])

        time.sleep(1)

        # SCROLL TO BOTTOM OF PAGE
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        job_links = []

        for x in range(int(total_jobs / 10) + 1):
            try:
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         '/html/body/div[1]/div/div/div[1]/main/div[2]/div/div/div/div/div[5]/button'))).click()
            except:
                pass

            jobs = WebDriverWait(driver, 10).until(
                EC.visibility_of_any_elements_located(
                    (By.CLASS_NAME, "css-bNzNOn")))
            print(len(jobs))
            lenOfPage = driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")

        job_links = [i.get_attribute('href') for i in jobs]

        with open('new_all_job_links.csv', 'w', encoding='utf8', newline='') as f:
            d = csv.writer(f)
            for row in job_links:
                d.writerow([row])

        job_data = []

        for n, link in enumerate(job_links, 1):
            if n > 1:
                break
            try:
                job_title = salary_avg = team = sub_team = location = ''
                role = tasks = qualifications = qualifications_plus = ''
                driver.get(link)
                time.sleep(1)
                page = driver.page_source
                soup = bs(page, 'lxml')

                if re.fullmatch('Intern ', soup.text):
                    print('internship formatting')
                    continue

                content = soup.find('div', attrs={'class': 'css-cvJeNJ'})

                if content:
                    job_title = soup.find('h1').text if soup.find('h1') else None

                    team_location = str(soup.find('div', attrs={'class': 'css-hCSdnY'})).split(
                        '<div class="css-cAElYq">', 1)

                    team = strip_html(team_location[0])
                    if re.search(',', team):
                        team, sub_team = team.split(', ')

                    if len(team_location) > 1:
                        location = strip_html(team_location[1])

                    if re.search('About the Role(.*?)What You Will Do', str(content.text), re.IGNORECASE):
                        role = re.search('About the Role(.*?)Will Do', str(content.text), re.IGNORECASE)[1]
                    elif re.search('About the Role(.*?)What the Candidate Will Do', str(content.text), re.IGNORECASE):
                        role = re.search('About the Role(.*?)What the Candidate Will Do', str(content.text), re.IGNORECASE)[1]
                    elif re.search('About the Role(.*?)What You’ll Do', str(content.text), re.IGNORECASE):
                        role = re.search('About the Role(.*?)What You’ll Do', str(content.text), re.IGNORECASE)[1]

                    # COLLECT ONLY SALARIES IN USD
                    if re.search('USD(.*?) per year\.', content.text):
                        salary_range = re.search('USD(.*?) per year\.', content.text)[0]
                        salary_low = int(salary_range.split(' - ')[0].replace(' per year', '').replace('USD$', '').replace(',', ''))
                        salary_high = int(salary_range.split(' - ')[1].replace(' per year.', '').replace('USD$', '').replace(',', ''))
                        salary_avg = (salary_high + salary_low) / 2

                    for c, x in enumerate(content.find_all('ul'), 1):
                        if c == 1:
                            tasks = ". ".join([itm.text for itm in x])
                        elif c == 2:
                            qualifications = ". ".join([itm.text for itm in x])
                        elif c == 3:
                            qualifications_plus = ". ".join([itm.text for itm in x])

                # FOR TESTING
                # print(link)
                # print('\t', job_title)
                # print('\t', team)
                # print('\t', sub_team)
                # print('\t', location)
                # print('\t', role)
                # print('\t', tasks)
                # print('\t', qualifications)
                # print('\t', qualifications_plus)
                # print('\t', salary_avg)

                # BUILD LIST
                job_data.append([link, job_title, salary_avg, team, sub_team, location, role, tasks, qualifications,
                                 qualifications_plus])

            except Exception as e:
                print(link)
                traceback.print_exc()

            # SAVE JOB DATA INTO CSV
            with open('all_job_data.csv', 'w', encoding='utf8', newline='') as f:
                d = csv.writer(f)
                for row in job_data:
                    d.writerow(row)

        driver.quit()

    except Exception as e:
        traceback.print_exc()
