from pydub import AudioSegment

class Exporter(object):
    options_template = ["title","album","artist","date","cover"]

    def __init__(self,pathtofile,options):
        self.path = pathtofile
        self.aformat = pathtofile[len(pathtofile)-3:]
        self.options = options
        self.checkoptions()
        self.audioseg = self.importaudio(pathtofile,self.aformat)

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

    def importaudio(self,path,aformat):
        """
        Import the downloadedfile/mp3 to an AudioSegment
        """
        return AudioSegment.from_file(path, aformat)

    def export(self,export_path):
        """
        Export the Audiosegment to an Audio file with Tages in options
        """
        tags = self.options.copy()
        tags.pop("cover")

        filename = export_path + self.aformat
        self.audioseg.export(filename,
                        format=self.aformat,
                        tags=tags,
                        cover=self.options["cover"])
        return "File: {0}, Options: {1}".format(filename,self.options)