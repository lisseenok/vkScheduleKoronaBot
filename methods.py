import json
import requests
import os
from bs4 import BeautifulSoup
import datetime
from matplotlib import pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter


def make_stat(link):
    url = "https://coronavirusstat.ru" + link
    need_dynamics = "russia" in link
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        # print(page)

        result = {}
        stat = soup.find("div", {"class": "row justify-content-md-center"})
        for elem in stat.find_all("div", {"class": "h2"}):
            total = elem.text
            name = elem["title"].split()[-1]
            result.update({name: {"total": "", "today": ""}})
            today = elem.find_parent().find("span", text="(сегодня)").find_parent().find("span").text
            result[name]["total"] = total
            result[name]["today"] = today

        message = f'По состоянию на {stat.find_parent().find("h6").find("strong").text}'
        for i in result.keys():
            message += f'\n{i}: {result[i]["total"]} ({result[i]["today"]} за сегодня)'

        print(message)

        if need_dynamics:
            dates = []
            dynamics = {"active": [],
                        "recovered": [],
                        "deaths": []}
            table = soup.find("table", {"class": "table table-bordered small"}).find("tbody")
            ci = 0
            for i in table.find_all("tr"):
                if ci == 0:
                    ci += 1
                    continue
                if ci == 11:
                    break

                date = i.find("th").text

                cc = 0
                dates.append(date)
                for count in i.find_all("td"):
                    if cc == 0:
                        dynamics["active"].append(int(count.text.split()[0]))
                    elif cc == 1:
                        dynamics["recovered"].append(int(count.text.split()[0]))
                    elif cc == 2:
                        dynamics["deaths"].append(int(count.text.split()[0]))
                    elif cc == 3:
                        break
                    cc += 1

                ci += 1

            print(dynamics)

            x = [datetime.datetime.strptime(i, '%d.%m.%Y').date() for i in dates]

            dataset1 = np.array(dynamics["active"])
            dataset2 = np.array(dynamics["recovered"])
            dataset3 = np.array(dynamics["deaths"])

            plt.bar(x, dataset1, color='tab:orange')
            plt.bar(x, dataset2, bottom=dataset1, color='tab:green')
            plt.bar(x, dataset3, bottom=dataset1 + dataset2, color='tab:red')
            plt.legend(["Активных", "Вылечено", "Умерло"])
            plt.title("Статистика за последние 10 дней")

            y_formatter = ScalarFormatter(useOffset=False)
            y_formatter.set_scientific(False)
            plt.gca().yaxis.set_major_formatter(y_formatter)
            plt.gcf().autofmt_xdate()

            plt.savefig('stat.png')

        return message
    except Exception:
        print(f"something wrong with {url}")
        return "BAD"


def find_group(group):
    # возвращает true если группа существует, и false в противном случае
    group = group.upper()
    found = False

    filepath = os.path.abspath(os.curdir) + "/tables/groups_schedule.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        file_data = json.load(file)

    course = datetime.datetime.now().year % 100 - int(group[-2:])
    if 1 <= course <= 4:
        for group_data in file_data["groups"]:
            if group_data["group"] == group:
                found = True
                break

    return found


def find_region(region):
    # возвращаем список регионов, которые в теории могут нам подойти
    region = region.lower()
    different_regions = []

    filepath = os.path.abspath(os.curdir) + "/tables/regions.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        regions = json.load(file)

    for ob in regions:
        if region in ob[1].lower():
            different_regions.append(ob)
            if len(different_regions) > 10:
                return different_regions

    return different_regions


def find_teacher(teacher):
    teacher = teacher.lower()
    different_teachers = []

    filepath = os.path.abspath(os.curdir) + "/tables/teachers.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        teachers = json.load(file)

    for t in teachers["teachers"]:
        if teacher in t.lower():
            if t not in different_teachers:
                different_teachers.append(t)
                if len(different_teachers) > 10:
                    return different_teachers

    return different_teachers
