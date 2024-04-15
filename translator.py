import deep_translator as deeptl

class Translator:
    def __init__(self, target: str) -> None:
        self.model = deeptl.GoogleTranslator(
            source='auto', target=target
        )
        self.trtime = 0.0
    
    def change_lang_src(self, lang_src: str):
        self.model.source = lang_src
    
    def change_lang_target(self, lang_target: str):
        self.model.target = lang_target

    def convert_to_string(self, textlist):
        # Very long string makes translation didn't apply to some string
        # It works properly if directly in the website
        # Need to be splitted into maybe 2 - 5 batch
        return " || ".join(textlist)

    def translate(self, texts):
        result = self.model.translate_batch(texts)
        return result
    
    def show_tr_duration(self):
        print(f"Translation time: {self.trtime}")