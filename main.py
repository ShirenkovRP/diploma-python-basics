import time
import json

import requests
from tqdm import tqdm


class UserVK:
    url = "https://api.vk.com/method/"

    def __init__(self, userid, token, version, album_id="profile"):
        self.userid = userid
        self.token = token
        self.version = version
        self.album_id = album_id
        self.params_photos = {
            "owner_id": self.userid,
            "access_token": self.token,
            "v": self.version,
            "album_id": self.album_id,
            "extended": "1"
        }

        # получение списка фотографий
        self.photos_get = requests.get(self.url + "photos.get", self.params_photos).json()["response"]["items"]

    # создадим список фотографий с максимальным размером
    def photos_max_size(self):
        photo_list = []
        for photos in self.photos_get:
            photo_dict = dict()
            photo_dict["url_photo"] = photos["sizes"][-1]["url"]
            photo_dict["sizes"] = photos["sizes"][-1]["type"]
            photo_dict["name_file"] = photos["likes"]["count"]
            photo_dict["date"] = photos["date"]
            photo_list.append(photo_dict)
        return photo_list

    # список альбомов
    def albums_list(self):
        params_albums = {
            "owner_id": self.userid,
            "access_token": self.token,
            "v": self.version,
        }
        try:
            albums_get = requests.get(self.url + "photos.getAlbums", params_albums).json()["response"]["items"]
            album_user = [{"title": "profile", "id": "profile", "size": len(self.photos_get)}]
            for album in albums_get:
                album_dict = dict()
                album_dict["title"] = album["title"]
                album_dict["id"] = album["id"]
                album_dict["size"] = album["size"]
                album_user.append(album_dict)
        except KeyError:
            album_user = [{"title": "profile", "id": "profile", "size": len(self.photos_get)}]

        return album_user


class YandexDisk:
    url_yandex = "https://cloud-api.yandex.net/v1/disk/resources"

    def __init__(self, token_ynd):
        self.token_ynd = token_ynd
        self.headers_yandex = {"Authorization": f"OAuth {self.token_ynd}"}

    # создаем список папок
    def list_dir(self):
        folder = requests.get(self.url_yandex,
                              params={"path": "/", "fields": "dir"},
                              headers=self.headers_yandex
                              ).json()
        list_folder = []
        for list_num in folder["_embedded"]["items"]:
            list_folder.append(list_num["name"])
        return list_folder

    # создание папки
    def new_folder_get(self, name_folder="photo_vk"):
        requests.put(self.url_yandex,
                     params={"path": f"/{name_folder}"},
                     headers=self.headers_yandex
                     ).json()

    # создаем список файлов на яндекс диске в папке "photo_vk"
    def list_file(self):
        if "photo_vk" not in self.list_dir():
            self.new_folder_get()
        files = requests.get(self.url_yandex,
                             params={"path": "/photo_vk"},
                             headers=self.headers_yandex
                             ).json()["_embedded"]
        new_list_file = []
        if files["total"] > 0:
            for list_num in files["items"]:
                new_list_file.append(list_num["name"])
        return new_list_file

    # запись файлов на диск
    def load_disk(self, list_photo, limit=5):
        if limit > len(list_photo):
            limit = len(list_photo)
        json_list = []

        print("Загрузка фотографий на яндекс диск")
        for i in tqdm(range(limit)):
            json_dict = {}
            value_list = list_photo[i]
            name_file = f"{value_list['name_file']}.jpg"
            if name_file in self.list_file():
                name_file = f"{value_list['name_file']}_{value_list['date']}.jpg"
            href = requests.get(self.url_yandex+"/upload",
                                params={"path": f"/photo_vk/{name_file}",
                                        "url": value_list["url_photo"],
                                        "overwrite": "true"},
                                headers=self.headers_yandex
                                ).json()["href"]
            file = requests.get(value_list["url_photo"]).content
            requests.put(href, files={"file": file})
            json_dict["file_name"] = name_file
            json_dict["size"] = value_list['sizes']
            json_list.append(json_dict)
            time.sleep(0.5)
        # создание файла .json
        with open("info_file.json", "w") as f:
            json.dump(json_list, f)


def show_album(arg):
    print("Список доступных ольбомов пользователя")
    cost = 1
    for i in arg:
        print(f"{cost} - {i['title']} в альбоме {i['size']} фоток")
        cost += 1


def int_input(arg):
    mess = " "
    while type(mess) != int:
        try:
            mess = int(input(arg))
        except ValueError:
            print("Должно быть целое число")
    return mess


user_id = input("Введите id пользователя vk: ")
token_yandex = input("Введите токен с Полигона Яндекс.Диска.: ")

token_vk = "958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008"
version_api_vk = "5.126"

user_vk = UserVK(user_id, token_vk, version_api_vk)
show_album(user_vk.albums_list())

album_id = None
album_name = int_input("Введите номер альбома: ")
while album_id is None:
    try:
        album_id = user_vk.albums_list()[album_name - 1]["id"]
    except IndexError:
        print("Альбома с таким номером не существует")
        show_album(user_vk.albums_list())
        album_name = int_input("Введите номер альбома: ")

user_vk = UserVK(user_id, token_vk, version_api_vk, album_id)
num_photo = int_input("Введите число фотографий для записи на диск: ")

list_photo = user_vk.photos_max_size()
yandex_disk = YandexDisk(token_yandex)
yandex_disk.load_disk(list_photo, num_photo)
