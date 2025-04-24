#  Copyright © [2024] 程序那些事
# 仅供学习与个人使用，禁止商业用途。

import requests
import os
from services.resource.resource_service import ResourceService
from const.video_const import Orientation
import re
from PIL import Image

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
workdir = os.path.join(script_dir, "../../resource")
workdir = os.path.abspath(workdir)

def download_image(img_url, save_path):
    resp = requests.get(img_url, stream=True)
    if resp.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Image downloaded: {save_path}")
    else:
        print(f"Failed to download image: {img_url}")

class MangadexService(ResourceService):
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.mangadex.org/manga"

    def get_headers(self):
        token = self.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def get_token(self):
        from config.config import my_config, save_config
        token = my_config['resource']['mangadex'].get('access_token', '')
        if not token:
            token = self.login()
        return token

    def login(self):
        from config.config import my_config, save_config
        url = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": my_config['resource']['mangadex']['client_id'],
            "client_secret": my_config['resource']['mangadex']['client_secret'],
            "username": my_config['resource']['mangadex']['username'],
            "password": my_config['resource']['mangadex']['password']
        }
        if not data["client_id"] or not data["client_secret"] or not data["username"] or not data["password"]:
            return None
        resp = requests.post(url, data=data)
        if resp.status_code == 200:
            token = resp.json()['access_token']
            my_config['resource']['mangadex']['access_token'] = token
            save_config()
            return token
        else:
            print("Mangadex登录失败：", resp.text)
            return None

    def search_manga(self, query, per_page=10):
        params = {
            "title": query,
            "limit": per_page
        }
        headers = self.get_headers()
        response = requests.get(self.base_url, params=params, headers=headers)
        if response.status_code == 401:
            # token失效，自动重登
            self.login()
            headers = self.get_headers()
            response = requests.get(self.base_url, params=params, headers=headers)
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                print(f"Mangadex API返回内容不是JSON，内容如下：\n{response.text}")
                return None
        else:
            print(f"Error: {response.status_code}")
            return None

    def get_chapters(self, manga_id, limit=1):
        url = f"https://api.mangadex.org/chapter"
        params = {"manga": manga_id, "limit": limit, "translatedLanguage[]": "en"}
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_chapter_images(self, chapter_id):
        url = f"https://api.mangadex.org/at-home/server/{chapter_id}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        return None

    def handle_video_resource(self, query, audio_length, per_page=10, exact_match=False):
        print("[Mangadex调试] handle_video_resource 入参:", query, audio_length, per_page, exact_match)
        # 1. 搜索漫画
        manga_data = self.search_manga(query, 1)
        print("[Mangadex调试] manga_data:", manga_data)
        if not manga_data or 'data' not in manga_data or not manga_data['data']:
            print("No manga found.")
            return [], 0
        manga_id = manga_data['data'][0]['id']
        print("[Mangadex调试] manga_id:", manga_id)
        # 2. 获取章节
        chapters = self.get_chapters(manga_id, 1)
        print("[Mangadex调试] chapters:", chapters)
        if not chapters or 'data' not in chapters or not chapters['data']:
            print("No chapters found.")
            return [], 0
        chapter_id = chapters['data'][0]['id']
        print("[Mangadex调试] chapter_id:", chapter_id)
        # 3. 获取章节图片
        images_info = self.get_chapter_images(chapter_id)
        print("[Mangadex调试] images_info:", images_info)
        if not images_info or 'chapter' not in images_info:
            print("No images found.")
            return [], 0
        base_url = images_info['baseUrl']
        hash_val = images_info['chapter']['hash']
        img_files = images_info['chapter']['data']  # 原图
        print("[Mangadex调试] img_files:", img_files)
        # 4. 下载图片到本地
        return_imgs = []
        if img_files:
            for idx, img_file in enumerate(img_files):
                img_url = f"{base_url}/data/{hash_val}/{img_file}"
                img_name = img_file.split('.')[-2]  # 取文件名主体
                save_name = os.path.join(workdir, f"mangadex-{chapter_id}-{img_name}.{img_file.split('.')[-1]}")
                print(f"[Mangadex调试] 下载图片: {img_url} -> {save_name}")
                download_image(img_url, save_name)
                return_imgs.append(save_name)
        else:
            print("No images in chapter.")
        print("[Mangadex调试] return_imgs:", return_imgs)
        # 5. 返回本地图片路径列表和总页数
        return return_imgs, len(return_imgs)

    def get_manga_and_chapters(self, query):
        import re
        uuid_pattern = re.compile(r'^[0-9a-fA-F-]{36}$')
        manga_id = None
        selected_chapter_id = None
        # 1. 判断是否为UUID
        if uuid_pattern.match(query):
            # 先查是不是漫画ID
            manga_info_resp = requests.get(f'https://api.mangadex.org/manga/{query}')
            if manga_info_resp.status_code == 200 and 'data' in manga_info_resp.json():
                manga_id = query
            else:
                # 查是不是章节ID
                chapter_resp = requests.get(f'https://api.mangadex.org/chapter/{query}')
                if chapter_resp.status_code == 200 and 'data' in chapter_resp.json():
                    for rel in chapter_resp.json()['data']['relationships']:
                        if rel['type'] == 'manga':
                            manga_id = rel['id']
                            selected_chapter_id = query
                            break
                if not manga_id:
                    return None, [], None
        else:
            # title查找
            manga_data = self.search_manga(query, 5)
            if manga_data and 'data' in manga_data and manga_data['data']:
                manga_id = manga_data['data'][0]['id']
            else:
                # 变体尝试
                alt_titles = [
                    query.replace(' ', ''),
                    query.lower(),
                    query.title(),
                ]
                found = False
                for alt in alt_titles:
                    manga_data = self.search_manga(alt, 5)
                    if manga_data and 'data' in manga_data and manga_data['data']:
                        manga_id = manga_data['data'][0]['id']
                        found = True
                        break
                if not found:
                    return None, [], None
        # 统一章节获取逻辑
        def fetch_feed(manga_id, with_lang=True):
            chapters = []
            offset = 0
            while True:
                params = {"limit": 100, "offset": offset}
                if with_lang:
                    params["translatedLanguage[]"] = ["en", "zh-hans", "zh", "ko", "ja"]
                resp = requests.get(f"https://api.mangadex.org/manga/{manga_id}/feed", params=params)
                if resp.status_code != 200:
                    break
                data = resp.json()
                if 'data' not in data or not data['data']:
                    break
                for ch in data['data']:
                    chapters.append({
                        "id": ch['id'],
                        "title": ch['attributes'].get('title', ''),
                        "chapter": ch['attributes'].get('chapter', ''),
                        "volume": ch['attributes'].get('volume', ''),
                        "translatedLanguage": ch['attributes'].get('translatedLanguage', '')
                    })
                if len(data['data']) < 100:
                    break
                offset += 100
            return chapters
        chapters = fetch_feed(manga_id, with_lang=True)
        if not chapters:
            chapters = fetch_feed(manga_id, with_lang=False)
        # 默认选中逻辑
        if selected_chapter_id:
            selected_idx = next((i for i, ch in enumerate(chapters) if ch['id'] == selected_chapter_id), 0)
        else:
            selected_idx = 0
        return manga_id, chapters, selected_idx

    def handle_video_resource_by_chapter(self, chapter_id):
        images_info = self.get_chapter_images(chapter_id)
        if not images_info or 'chapter' not in images_info:
            print("No images found.")
            return [], 0
        base_url = images_info['baseUrl']
        hash_val = images_info['chapter']['hash']
        img_files = images_info['chapter']['data']
        return_imgs = []
        for idx, img_file in enumerate(img_files):
            img_url = f"{base_url}/data/{hash_val}/{img_file}"
            img_name = img_file.split('.')[-2]
            save_name = os.path.join(workdir, f"mangadex-{chapter_id}-{img_name}.{img_file.split('.')[-1]}")
            download_image(img_url, save_name)
            img = Image.open(save_name)
            width, height = img.size
            target_width = 1080
            target_height = 1920
            overlap = 200
            # 只保留高宽比大于2的图片（正文），其余跳过
            if height / width < 2:
                print(f"跳过非正文图片: {save_name}")
                continue
            # 先等比缩放宽度到1080
            if width != target_width:
                scale_ratio = target_width / width
                new_height = int(height * scale_ratio)
                img = img.resize((target_width, new_height), Image.LANCZOS)
                width, height = img.size
            # 如果图片高度小于目标高度，pad补齐
            if height <= target_height:
                from PIL import ImageOps
                pad_img = ImageOps.pad(img, (target_width, target_height), color=(0,0,0))
                cut_name = save_name.replace('.', f'-cut0.')
                pad_img.save(cut_name)
                return_imgs.append(cut_name)
            else:
                # 按1920像素一段切割，重叠overlap像素
                start = 0
                cut_idx = 0
                while start < height:
                    end = min(start + target_height, height)
                    box = (0, start, target_width, end)
                    cut_img = img.crop(box)
                    # 切割后如果内容高度不足目标高度一半，也跳过
                    if cut_img.size[1] < target_height // 2:
                        start += target_height - overlap
                        cut_idx += 1
                        continue
                    # 如果最后一段不足1920高，pad补齐
                    if cut_img.size[1] < target_height:
                        from PIL import ImageOps
                        cut_img = ImageOps.pad(cut_img, (target_width, target_height), color=(0,0,0))
                    cut_name = save_name.replace('.', f'-cut{cut_idx}.')
                    cut_img.save(cut_name)
                    return_imgs.append(cut_name)
                    if end == height:
                        break
                    start += target_height - overlap
                    cut_idx += 1
        return return_imgs, len(return_imgs) 