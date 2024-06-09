import time
import torch
import asyncio
import os
import deep_translator as deeptl
from google.cloud import translate_v2 as translate
# from easynmt import EasyNMT

SEPARATOR = ' _|_ '
class Translator:
    def __init__(self, src: str, target: str) -> None:
        self.exec_time = 0.0
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
        print(f"Translation time: {self.exec_time}")
    
    def get_tr_duration(self):
        return self.exec_time

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
        self.exec_time = time.time() - start
        return res
    
    async def asynctranslate(self, texts: list[str]):
        res = self.translate(texts=texts)
        self.show_tr_duration()
        for text in res:
            yield text

class GoogleTranslator(Translator):
    def __init__(self, src: str, target: str) -> None:
        super().__init__(src=src, target=target)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'config/trkey.json'
        self.tlclient = translate.Client()

    def chinese_code_map(self) -> None:
        if self.target_lang == "ch_sim": self.target_lang = "zh-CN"
        elif self.target_lang == "ch_tra": self.target_lang = "zh-TW"

    def translate(self, texts:list[str]) -> list[str]:
        start = time.time()
        self.chinese_code_map()

        if len(texts) <= 128: translated = self.executetl_normal(texts)
        else: translated = self.executetl_splitted(texts)

        self.exec_time = time.time() - start
        return translated

    def executetl_normal(self, texts:list[str]) -> list[str]:
        response = self.tlclient.translate(
            texts, 
            target_language=self.target_lang
        )
        translated = [tled['translatedText'] for tled in response]
        return translated
    
    def executetl_splitted(self, texts:list[str]) -> list[str]:
        tledres = []
        iternum = len(texts) // 128 + 1
        start, end = 0, 127
        for x in range(iternum):
            if x == iternum-1:
                end = len(texts)-1
            response = self.tlclient.translate(
                texts[start:end], 
                target_language=self.target_lang
            )
            tledres += [tled['translatedText'] for tled in response]
            start += 128
            end += 128
        return tledres

    
    async def asynctranslate(self, texts: list[str]):
        for text in texts:
            translation = self.model.translate(text)
            yield translation