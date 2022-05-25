import json
import requests
import os
from PIL import Image
import datetime

my_api = "65adc8a5a4b8ab7d3ee70f4fa91cf498"  # WARNING no weather api
city_id = "524901"  # moscow


def wind_direction(degrees):
    if degrees < 22.5:
        return "С"
    if degrees < 45 + 22.5:
        return "СВ"
    if degrees < 90 + 22.5:
        return "В"
    if degrees < 135 + 22.5:
        return "ЮВ"
    if degrees < 180 + 22.5:
        return "Ю"
    if degrees < 225 + 22.5:
        return "ЮЗ"
    if degrees < 270 + 22.5:
        return "З"
    if degrees < 315 + 22.5:
        return "СЗ"
    return "С"


def wind_strength(speed):
    if speed < 0.5:
        return "штиль"
    if speed < 1.5:
        return "тихий"
    if speed < 3:
        return "легкий"
    if speed < 5:
        return "слабый"
    if speed < 8:
        return "умеренный"
    if speed < 10:
        return "свежий"
    if speed < 14:
        return "сильный"
    if speed < 17:
        return "крепкий"
    if speed < 20:
        return "очень крепкий"
    if speed < 25:
        return "шторм"
    if speed < 33:
        return "сильный шторм"
    return "ураган"


def formatted_weather(description,
                      temperature,
                      feels_like,
                      pressure,
                      humidity,
                      visibility,
                      wind_deg,
                      wind_speed):
    return f"{description}, {round(temperature)}°C" \
           f"\n\nощущается как {round(feels_like)}°C" \
           f"\nдавление {round(pressure * 0.750064)} мм рт. ст." \
           f"\nвлажность {humidity}%" \
           f"\nвидимость {visibility // 1000}км" \
           f"\nветер {wind_direction(wind_deg)}, " \
           f"{wind_strength(wind_speed)}, " \
           f"{round(wind_speed)}м/с"


def make_weather_message(date):
    print(f"погода в Москве на {date}")
    today = f"{datetime.datetime.now():%Y-%m-%d}"
    tomorrow = f"{(datetime.datetime.now() + datetime.timedelta(days=1)):%Y-%m-%d}"
    after_tom = f"{(datetime.datetime.now() + datetime.timedelta(days=2)):%Y-%m-%d}"
    # print(today, tomorrow, after_tom)

    if date == "NOW":
        url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={my_api}&units=metric&lang=ru"
    else:
        url = f"http://api.openweathermap.org/data/2.5/forecast?id={city_id}&appid={my_api}&units=metric&lang=ru"

    try:
        response_weather = requests.get(url)
        weather = response_weather.json()
        icons = []
        result = []

        if date == "NOW":
            current_weather = weather
            iconcode = current_weather['weather'][0]['icon']
            iconurl = f"https://openweathermap.org/img/wn/{iconcode}@2x.png"

            icons.append(iconurl)

            result.append("СЕЙЧАС\n\n" + formatted_weather(current_weather['weather'][0]['description'],
                                            current_weather['main']['temp'],
                                            current_weather['main']['feels_like'],
                                            current_weather['main']['pressure'],
                                            current_weather['main']['humidity'],
                                            current_weather['visibility'],
                                            current_weather['wind']['deg'],
                                            current_weather['wind']['speed']))

        elif date == "TOD":
            i = 0

            time_good = [today + " 06:00:00",
                         today + " 12:00:00",
                         today + " 18:00:00",
                         tomorrow + " 00:00:00"]

            for current_weather in weather['list']:
                if current_weather['dt_txt'] not in time_good:
                    continue

                iconcode = current_weather['weather'][0]['icon']

                iconurl = f"https://openweathermap.org/img/wn/{iconcode}@2x.png"

                i += 1
                icons.append(iconurl)

                message = ""
                for time in range(4):
                    if current_weather['dt_txt'] == time_good[time]:
                        if time == 0:
                            message = "УТРО\n\n"
                        elif time == 1:
                            message = "ДЕНЬ\n\n"
                        elif time == 2:
                            message = "ВЕЧЕР\n\n"
                        else:
                            message = "НОЧЬ\n\n"

                message += formatted_weather(current_weather['weather'][0]['description'],
                                             current_weather['main']['temp'],
                                             current_weather['main']['feels_like'],
                                             current_weather['main']['pressure'],
                                             current_weather['main']['humidity'],
                                             current_weather['visibility'],
                                             current_weather['wind']['deg'],
                                             current_weather['wind']['speed'])

                result.append(message)
                if i == 4:
                    break

        elif date == "TOM":
            i = 0

            time_good = [tomorrow + " 06:00:00",
                         tomorrow + " 12:00:00",
                         tomorrow + " 18:00:00",
                         after_tom + " 00:00:00"]

            for current_weather in weather['list']:
                if current_weather['dt_txt'] not in time_good:
                    continue

                iconcode = current_weather['weather'][0]['icon']
                iconurl = f"https://openweathermap.org/img/wn/{iconcode}@2x.png"

                i += 1
                icons.append(iconurl)

                if i == 1:
                    message = "УТРО\n\n"
                elif i == 2:
                    message = "ДЕНЬ\n\n"
                elif i == 3:
                    message = "ВЕЧЕР\n\n"
                else:
                    message = "НОЧЬ\n\n"

                message += formatted_weather(current_weather['weather'][0]['description'],
                                             current_weather['main']['temp'],
                                             current_weather['main']['feels_like'],
                                             current_weather['main']['pressure'],
                                             current_weather['main']['humidity'],
                                             current_weather['visibility'],
                                             current_weather['wind']['deg'],
                                             current_weather['wind']['speed'])
                result.append(message)
                if i == 4:
                    break

        else:
            time_good = []
            for i in range(1, 6):
                time_good.append(f"{(datetime.datetime.now() + datetime.timedelta(days=i)):%Y-%m-%d} 00:00:00")
                time_good.append(f"{(datetime.datetime.now() + datetime.timedelta(days=i)):%Y-%m-%d} 12:00:00")

            for current_weather in weather['list']:
                if current_weather['dt_txt'] not in time_good:
                    continue

                iconcode = current_weather['weather'][0]['icon']
                iconurl = f"https://openweathermap.org/img/wn/{iconcode}@2x.png"

                icons.append(iconurl)

                is_day = current_weather['dt_txt'][11:] == "12:00:00"
                if is_day:
                    message = current_weather['dt_txt'][8:10] + "/" + current_weather['dt_txt'][5:7] + "\n"
                    message += "ДЕНЬ "
                else:
                    message = "НОЧЬ "

                message += f"{round(current_weather['main']['temp'])}°C"

                result.append(message)

            icon_counter = 0
            for i in range(0, len(icons) - 1, 2):
                iconurl1 = icons[i+1]
                iconurl2 = icons[i]
                response_icon1 = requests.get(iconurl1)
                response_icon2 = requests.get(iconurl2)
                iconpath1 = os.path.abspath(os.curdir) + "/icons/icon_current" + str(i) + ".png"
                iconpath2 = os.path.abspath(os.curdir) + "/icons/icon_current" + str(i+1) + ".png"
                with open(iconpath1, 'wb') as f:
                    f.write(response_icon1.content)

                with open(iconpath2, 'wb') as f:
                    f.write(response_icon2.content)

                img1 = Image.open(iconpath1, 'r')
                img2 = Image.open(iconpath2, 'r')
                img_w, img_h = img1.size
                background = Image.new('RGBA', (img_w * 2 + 24, img_h), (255, 255, 255, 255))
                offset = (img_w+12, 0)
                background.paste(img1, (12, 0))
                background.paste(img2, offset)

                savepath = os.path.abspath(os.curdir) + "/icons/icon_double" + str(icon_counter) + ".png"
                icon_counter += 1
                background.save(savepath)

            icons = []

        return {"message": result, "icons": icons}

    except ConnectionError:
        print("Ошибка доступа")
