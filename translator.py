import deep_translator as deeptl
import time
import asyncio

SEPARATOR = " TOKEN "
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
        # Separator often didn't perserve after translation
        return SEPARATOR.join(textlist)

    def translate(self, texts):
        start = time.time()
        texts = self.convert_to_string(texts)
        print(texts)
        result = self.model.translate(texts)
        self.trtime = time.time() - start
        return result.split(SEPARATOR)
    
    async def asynctranslate(self, texts: list[str]):
        for text in texts:
            translation = self.model.translate(text)
            yield translation
    
    def show_tr_duration(self):
        print(f"Translation time: {self.trtime}")