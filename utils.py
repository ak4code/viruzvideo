from urllib.parse import urlencode
import os
import requests
from http.cookies import SimpleCookie
import ffmpeg
from slugify import slugify

class ViruzVideo:
    VIDEO_FOLDER = 'videos'
    fetch = requests.Session()

    def __init__(self, cookies_file="cookies.txt"):
        self.cookies_file = cookies_file

    def set_video_folder(self, name):
        self.VIDEO_FOLDER = name

    async def _get_cookies(self):
        with open(self.cookies_file, "r") as f:
            raw_cookie = f.readline()
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        cookies = {}
        for key, morsel in cookie.items():
            cookies[key] = morsel.value
        return cookies

    async def _clean_video_folder(self):
        for file in os.scandir(self.VIDEO_FOLDER):
            os.remove(file.path)
        return print('Folder clean!')

    async def search_videos(self, keyword='test'):
        query = {
            "keyword": keyword,
            "app_language": "en-US",
            "priority_region": "EN",
            "region": "EN",
            "browser_language": "en-US"
        }
        path = 'https://t.tiktok.com/api/search/general/full/?aid=1988&{}'.format(urlencode(query))
        cookies = await self._get_cookies()
        req = self.fetch.get(path, cookies=cookies)
        json_data = req.json()
        return [item.get('item') for item in json_data.get('data') if item.get('type') == 1]

    @staticmethod
    async def concatenated_video(files):
        streams = []
        for file in files:
            streams.append(ffmpeg.input(file).video)
            streams.append(ffmpeg.input(file).audio)
        return (
            ffmpeg
            .concat(*streams, v=1, a=1)
            .filter('fps', fps=25, round='up')
            .output('videos/out.mp4', vsync='vfr')
            .run(overwrite_output=True)
        )

    @staticmethod
    async def processing_video(filename):
        stream = ffmpeg.input('videos/out.mp4')
        v = stream.video
        a = stream.audio
        v = v.filter('scale', 'ih*16/9', -1)
        v = v.filter('boxblur', luma_radius='min(h,w)/20', luma_power=1, chroma_radius='min(cw, ch)/20', chroma_power=1)
        v = v.filter('crop', h='iw*9/16')
        v = ffmpeg.overlay(v, stream.video, x='(W-w)/2', y='(H-h)/2')
        v = v.filter('scale', size='hd720', force_original_aspect_ratio='increase')
        v = v.filter('fps', fps=25, round='up')
        out = ffmpeg.output(v, a, f'output/{filename}.mp4', vsync='vfr')
        out.run(overwrite_output=True)

    async def video_downloading(self, data):
        video_files = []
        duration = 0
        for item in data:
            video = item.get('video')
            if duration > 240:
                break
            if video.get('height') == 1024:
                print(video)
                try:
                    response = self.fetch.get(video.get('downloadAddr'), cookies=await self._get_cookies())
                except requests.exceptions.SSLError:
                    continue
                filename = f"{self.VIDEO_FOLDER}/{video.get('id')}.mp4"
                video_files.append(filename)
                duration += video.get('duration')
                print(f"{filename} saved!")
                with open(filename, "wb") as file:
                    file.write(response.content)
        return video_files

    async def get_video(self, keyword, bot):
        print(F'Поиск по слову: {keyword}')
        await self._clean_video_folder()
        await bot.answer(f'Поиск видео для загрузки! Тэг: {bot.text}.')
        try:
            data = await self.search_videos(keyword)
        except:
            return 'Ошибка! Попробуйте снова!'
        await bot.answer('Подготовка к загрузке!')
        files = await self.video_downloading(data)
        await bot.answer(f'Видео загружены! Кол-во файлов: {len(files)}.')
        await bot.answer('Объединение видео! Ожидайте 5-10 минут!')
        await self.concatenated_video(files)
        await bot.answer('Объединение завершено!')
        await bot.answer('Обработка видео! Ожидайте 10-15 минут!')
        # filename = slugify(keyword)
        filename = 'out'
        await self.processing_video(filename)
        await bot.answer('Обработка завершена!')
        await bot.answer('Отправляю видеофайл!')
        await bot.answer_video(open(f'output/{filename}.mp4', 'rb'))
        return 'Задание выполнено!'
