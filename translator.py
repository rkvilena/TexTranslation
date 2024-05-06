import time
import torch
import asyncio
import os
import deep_translator as deeptl
from google.cloud import translate_v2 as translate
from easynmt import EasyNMT

SEPARATOR = ' _|_ '
class Translator:
    def __init__(self, src: str, target: str) -> None:
        self.trtime = 0.0
        self.src_lang = src
        self.target_lang = target
    
    def change_lang_src(self, lang_src: str):
        self.src_lang = lang_src
    
    def change_lang_target(self, lang_target: str):
        self.target_lang = lang_target

    def convert_to_string(self, textlist):
        # Very long string makes translation didn't apply to some string
        # It works properly if directly in the website
        # Separator often didn't perserve after translation
        return SEPARATOR.join(textlist)
    
    def show_tr_duration(self):
        print(f"Translation time: {self.trtime}")

STR_MODEL = 'mbart50_m2m'
class EasyNMTranslator(Translator):
    def __init__(self, src: str, target: str) -> None:
        super().__init__(src=src, target=target)
        self.model = EasyNMT(STR_MODEL)
        self.model.translate("", source_lang=src, target_lang=target)

    def translate(self, texts:list[str]) -> list[str]:
        torch.cuda.empty_cache()
        start = time.time()
        res = self.model.translate(
            texts, 
            source_lang=self.src_lang, 
            target_lang=self.target_lang,
            batch_size=5,
            show_progress_bar=False
        )
        self.trtime = time.time() - start
        return res
    
    async def asynctranslate(self, texts: list[str]):
        res = self.translate(texts=texts)
        self.show_tr_duration()
        for text in res:
            yield text

class GoogleTranslator(Translator):
    def __init__(self, src: str, target: str) -> None:
        super().__init__(src=src, target=target)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'trkey.json'
        self.tlclient = translate.Client()

    def translate(self, texts:list[str]) -> list[str]:
        start = time.time()
        response = self.tlclient.translate(
            texts, 
            target_language=self.target_lang
        )
        translated = [tled['translatedText'] for tled in response]
        self.trtime = time.time() - start
        return translated
    
    async def asynctranslate(self, texts: list[str]):
        for text in texts:
            translation = self.model.translate(text)
            yield translation