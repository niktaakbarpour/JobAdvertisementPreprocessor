class Lexicon:
    def __init__(self, dictionary_file_name: str, text_delimiter: str = " ", dictionary_delimiter: str = ":"):
        self.text_delimiter = text_delimiter
        all_pairs = open(dictionary_file_name, encoding='utf-8', newline='\n').read().strip().split("\n")
        self.dictionary = {}
        for word in all_pairs:
            pair = word.split(dictionary_delimiter)
            self.dictionary[pair[0]] = pair[1]
        pass

    def translate(self, word: str) -> str:
        if word in self.dictionary:
            return self.dictionary.get(word)
        else:
            return word
