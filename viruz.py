from slugify import slugify
from urllib.parse import urlencode
import os
import requests
from http.cookies import SimpleCookie
import ffmpeg


class ViruzVideo:
    VIDEO_INPUT_FOLDER = 'video_input'
    VIDEO_OUTPUT_FOLDER = 'video_output'
    fetch = requests.Session()

    def __init__(self, cookies_file="cookies.txt"):
        self.cookies_file = cookies_file

    def _get_cookies(self):
        with open(self.cookies_file, "r") as f:
            raw_cookie = f.readline()
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        cookies = {}
        for key, morsel in cookie.items():
            cookies[key] = morsel.value
        return cookies

    def _clean_video_folder(self):
        for file in os.scandir(self.VIDEO_FOLDER):
            os.remove(file.path)
        return print('Folder clean!')

    def search_videos(self, keyword='test', cursor=12):
        offset = cursor - 12
        query = {
            "keyword": keyword,
            "cursor": cursor,
            "offset": offset,
            "app_language": "en-US",
            "priority_region": "EN",
            "region": "EN",
            "browser_language": "en-US"
        }
        path = 'https://t.tiktok.com/api/search/general/full/?aid=1988&{}'.format(urlencode(query))
        cookies = self._get_cookies()
        req = self.fetch.get(path, cookies=cookies)
        json_data = req.json()
        return [item.get('item') for item in json_data.get('data') if item.get('type') == 1]

    def video_downloading(self, data):
        video_files = []
        duration = 0
        for item in data:
            video = item.get('video')
            # if duration > 300:
            #     break
            if video.get('height') == 1024:
                print(video)
                try:
                    response = self.fetch.get(video.get('downloadAddr'), cookies=self._get_cookies())
                except requests.exceptions.SSLError:
                    continue
                filename = f"{self.VIDEO_INPUT_FOLDER}/{video.get('id')}.mp4"
                video_files.append(filename)
                duration += video.get('duration')
                print(f"{filename} saved!")
                with open(filename, "wb") as file:
                    file.write(response.content)
        return video_files

    def concatenated_video(self, files):
        streams = []
        for file in files:
            streams.append(ffmpeg.input(file).video)
            streams.append(ffmpeg.input(file).audio)
        return (
            ffmpeg
                .concat(*streams, v=1, a=1)
                .filter('fps', fps=25, round='up')
                .output(f'{self.VIDEO_INPUT_FOLDER}/out.mp4', vsync='vfr')
                .run(overwrite_output=True)
        )

    def processing_video(self, filename):
        stream = ffmpeg.input(f'{self.VIDEO_INPUT_FOLDER}/out.mp4')
        v = stream.video
        a = stream.audio
        v = v.filter('scale', 'ih*16/9', -1)
        v = v.filter('boxblur', luma_radius='min(h,w)/20', luma_power=1, chroma_radius='min(cw, ch)/20', chroma_power=1)
        v = v.filter('crop', h='iw*9/16')
        v = ffmpeg.overlay(v, stream.video, x='(W-w)/2', y='(H-h)/2')
        v = v.filter('scale', size='hd720', force_original_aspect_ratio='increase')
        v = v.filter('fps', fps=25, round='up')
        out = ffmpeg.output(v, a, f'{self.VIDEO_OUTPUT_FOLDER}/{filename}.mp4', vsync='vfr')
        out.run(overwrite_output=True)

    def get_video(self, keyword, count):
        print(F'Поиск по слову: {keyword}')
        cursor = 12
        cursor = cursor * count

        print(F'Курсор: {cursor}')

        try:
            data = self.search_videos(keyword, cursor)
        except:
            return print('Ошибка! Попробуйте снова!')

        files = self.video_downloading(data)

        self.concatenated_video(files)

        filename = f'{slugify(keyword)}-{count}'
        self.processing_video(filename)

        return print(f'Задание #{count} выполнено!')


def main():
    vv = ViruzVideo()
    for count in range(3, 10):
        vv.get_video(keyword='смешно', count=count)


if __name__ == '__main__':
    main()
