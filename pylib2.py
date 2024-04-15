from translator import Translator
import time
from textdetrec import TextDetectionRecognition
from deep_translator import GoogleTranslator

if __name__ == '__main__':
    while True:
        # tdr = TextDetectionRecognition(['en'])
        tl = Translator('id')

        # tdr.load_image_file(str(input()))
        # start = time.time()
        # tdr.scan()
        # res = tdr.get_result()
        str = ['「最近', 'どんどん電波入んなくなってるなあ」', '「せっかくスマホ充電できたのに', '…」', '「てれじゃ写真とるくらいしかやるてとないじゃん」', 'でむ', 'せっかくだからてのま ま録音しよっかな」']
        translated = tl.translate(texts=str)
        # print(res[0])
        print(str)
        print(translated)
        # print("Exec duration : ", time.time() - start)
        print("Length : ", len(translated))
        break