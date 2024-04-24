import deep_translator as deeptl
import time

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

    def translate(self, texts):
        start = time.time()
        result = self.model.translate_batch(texts)
        print(time.time() - start)
        return result
    
    def show_tr_duration(self):
        print(f"Translation time: {self.trtime}")