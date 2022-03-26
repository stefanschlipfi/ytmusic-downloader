import json,re,os
import youtube_dl
from requests import request
from PIL import Image
from exporter import Exporter

class YTMusic_Downloader:

    def __init__(self,url):

        #TODO check if is link
        self.url = url
        self.config = self.load_settings()
        self.option_template = {"title":"title","album":"album","artist":"artist","date":"release_year","cover":"thumbnails"}
        self.cutter_regex_comp = re.compile(r"(\[|\().*(\)|\])")
        self.filler_regex_comp = re.compile(r"[^a-zA-Z0-9\s\-]")

    def load_settings(self):

        settings_path = './settings.json'
        if not os.path.exists(settings_path):
            settings_path = '/etc/ytmusic-downloader/settings.json'

        try:
            with open(settings_path,'r') as jf:
                return json.load(jf)
        except Exception as e:
            raise e

    def flat_playlist(self,options = {'playlist_items': '0-100'}):
        """
        flat playlist return list with urls
        """
        ydl_opts = {'extract_flat' : True}
        ydl_opts.update(options)

        playlist_urls = set()
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(self.url, download=False)
            
            if "entries" in playlist_info:
                for entries in playlist_info['entries']:
                    playlist_urls.add("https://music.youtube.com/watch?v={0}".format(entries["url"]))
            else:
                playlist_urls = {self.url}

            return playlist_urls

    def download_url(self,url,download=True, maxdownloadretries=3):
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
            'outtmpl':self.config['temp_dir'] + '/%(id)s.%(ext)s',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=download)
            except Exception as e:
                print("Error on url: {0}\nException: {1}".format(url,e))
                if maxdownloadretries > 0:
                   print("New Attempt! Max Tries: " + str(maxdownloadretries))
                   return self.download_url(url,download,maxdownloadretries-1)
                else:
                   print("Error: Impossible to download " + url)
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
                options.update({"ytdl_tmp_path": "{}/{}.{}".format(self.config['temp_dir'],info_dict["id"],ydl_opts["postprocessors"][0]["preferredcodec"])})
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

    def pretty_path(self,path):
        path = re.sub(self.cutter_regex_comp,"",path)
        path = re.sub(self.filler_regex_comp, "", path)
        path = path.strip() 

        #replace spaces with underscore
        path = re.sub(r"\s+","_",path)
        return path


    def main(self):

        flat_playlist_settings = self.config.get('flat_playlist_settings')
        if not flat_playlist_settings:
            flat_playlist_settings = {'playlist_items': '0-100'}

        download_list = self.flat_playlist(options=flat_playlist_settings)
        downloaded_songs = list()
        for song_url in download_list:
            resp = self.download_url(song_url,download=True)
            if resp[0]:
               downloaded_songs.append(resp[1])
        

        for song_dict in downloaded_songs:

            #Manual Tags
            #song_dict["album"] = "Ultimate Christmas Hits"
            artist = song_dict["artist"]
            #artist = ""
            #Is a cover wanted?
            coverwanted = True

            #define export dir without title
            export_dir = "{0}/{1}/{2}/".format(\
                 self.pretty_path(self.config["export_dir"]) \
                ,self.pretty_path(artist) \
                ,self.pretty_path(song_dict["album"]))

            #check if path exists
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            #append title
            export_path = export_dir + self.pretty_path(song_dict["title"])

            #debug
            print("Export_Path: " + export_path)

            #convert cover
            resp_cover = self.download_crop_cover(song_dict["cover"])

            if coverwanted and resp_cover[0]: 
                song_dict.update({"cover":resp_cover[1]})
            else:
                song_dict.update({"cover":None})

            ytdl_tmp_path = song_dict.pop("ytdl_tmp_path")
                
            try:
                print(song_dict)
                exporter = Exporter(ytdl_tmp_path,song_dict)
                exporterlog = exporter.export(export_path)
            except Exception as e:
                print("skipped: {0}\nError: {1}".format(ytdl_tmp_path,e))
            else:
                print("successfully exported: {0}\n{1}".format(song_dict["title"],exporterlog))

        print("Downloaded {0}:songs from url: {1}".format(len(downloaded_songs),self.url))

if __name__ == "__main__":
    url = input("Enter Youtube Music URL: ")
    s = YTMusic_Downloader(url)
    s.main()
