class File:
    @staticmethod
    def from_file(filename=""):
        straeng = ""
        try:
            f = open(filename, "r+")
            
            for l in f:
                straeng += l + '\n'

            f.close()

            return straeng
        except FileNotFoundError:
            print(f"oOf. {filename} does not exist.")
            return None

    def to_file(filename, content):
        #file_exists = os.path.exists(filename)

        f = open(filename, "w+")
        f.write(content)
        f.close()

#https://github.com/Kayden143/Hack112
