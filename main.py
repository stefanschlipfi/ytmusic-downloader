import json,re,os
import youtube_dl
from requests import request
from PIL import Image
from exporter import Exporter

class Converter:

    def __init__(self,url):

        #TODO check if is link
        self.url = url
        self.base_dir = "/opt/ytmusic-downloader/"
        self.config = self.load_settings()
        self.option_template = {"title":"title","album":"album","artist":"artist","year":"release_year","cover":"thumbnails"}


    def load_settings(self):

        try:
            with open(self.base_dir + 'settings.json','r') as jf:
                return json.load(jf)
        except Exception as e:
            raise e

    def flat_playlist(self,options = {'playlist_items': '0-100'}):
        """
        flat playlist return list with urls
        """
        ydl_opts = {'extract_flat' : True}
        ydl_opts.update(options)

        playlist_urls = []
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(self.url, download=False)
            
            if "entries" in playlist_info:
                for entries in playlist_info['entries']:
                    playlist_urls.append("https://music.youtube.com/watch?v={0}".format(entries["url"]))
            else:
                playlist_urls = [self.url]

            return playlist_urls

    def download_url(self,url,download=True):
        """
        download from self.link
        return bool list with title_informations
        """    
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist' : True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl':self.config['temp_dir'] + '/%(title)s-%(id)s.%(ext)s',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=download)
            except Exception as e:
                print("Error on url: {0}\nException: {1}".format(url,e))
                return False,e
            else:
                options = {}
                for to_key, yt_key in self.option_template.items():
                    try:
                        info_op = info_dict[yt_key]
                        if to_key == "artist":
                            info_op = re.sub(r',.*','',info_op)
                        if to_key == "cover":
                            info_op = info_op[len(info_op)-1]["url"]
                    except KeyError:
                        info_op = ""
                    finally:
                        options.update({to_key:info_op})
                options.update({"file_path": "{0}/{1}-{2}.{3}".format(self.config['temp_dir'],info_dict["title"],info_dict["id"],ydl_opts["postprocessors"][0]["preferredcodec"])})
                return True,options

    def download_crop_cover(self,url):
        """
        download image from url and crop it
        return bool, image_path
        """

        image = request("GET",url)
        if not image:
            return False,"Failed with status_code: {0}, url: {1}".format(image.status_code,image.url)

        with open(self.config["temp_dir"] + "/image",'wb') as f:
            f.write(image.content)

        image = Image.open(self.config["temp_dir"] + "/image").convert("RGB")
        left = int((image.width - image.height) / 2)
        right = int(image.width - left)
        
        croped_image = image.crop((left,0,right,image.height))
        croped_image.thumbnail((720,720))
        croped_image.save(self.config["temp_dir"] + "/image_croped.png")
        return True,self.config["temp_dir"] + "/image_croped.png"

    def main(self):
        download_list = self.flat_playlist()
        downloaded_songs = list()
        for song_url in download_list:
            resp = self.download_url(song_url)
            if resp[0]:
                downloaded_songs.append(resp[1])
        
        for song_dict in downloaded_songs:
            export_path = "{}/{}/{}/".format(self.config["export_dir"],song_dict["artist"],song_dict["album"])

            #check if path exists
            if not os.path.exists(export_path):
                os.makedirs(export_path)

            #convert cover
            resp_cover = self.download_crop_cover(song_dict["cover"])
            if resp_cover[0]:
                song_dict.update({"cover":resp_cover[1]})
                file_path = song_dict.pop("file_path")
                
                try:
                    e = Exporter(file_path,song_dict)
                    e.export(export_path)
                except Exception as e:
                    print("skipped: {0}\nError: {1}".format(file_path,e))
                else:
                    print("successfully converted: {0}".format(song_dict["title"]))

        print("Downloaded {0}:songs from url: {0}".format(len(downloaded_songs),self.url))

if __name__ == "__main__":
    url = input("Enter Youtube Music URL: ")
    s = Converter(url)
    s.main()