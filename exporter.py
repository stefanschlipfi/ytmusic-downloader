from pydub import AudioSegment

class Exporter(object):
    options_template = ["title","album","artist","date","cover"]

    def __init__(self,pathtofile,options):
        self.path = pathtofile
        self.audio_format = pathtofile[len(pathtofile)-3:] # mp3
        self.options = options
        self.checkoptions()
        self.audioseg = self.importaudio(pathtofile,self.audio_format)

    def checkoptions(self):
        """
        Check if the options dict is valable
        """
        key_list = list(self.options.keys())
        i = 0
        for opttemp in self.options_template:
            if not opttemp == key_list[i]:
                raise KeyError("Options in wrong Format -->" + opttemp + ":" + key_list[i])
            i += 1

    def importaudio(self,path,audio_format):
        """
        Import the downloadedfile/mp3 to an AudioSegment
        """
        return AudioSegment.from_file(path, audio_format)

    def export(self,export_path):
        """
        Export the Audiosegment to an Audio file with Tages in options
        """
        cover = self.options.pop("cover")
        filename = export_path + "." +self.audio_format
        self.audioseg.export(filename,
                        format=self.audio_format,
                        tags=self.options,
                        cover=cover)
        return "File: {0}, Options: {1}".format(filename,self.options)