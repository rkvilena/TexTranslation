from translator import Translator
import time
from textdetrec import TextDetectionRecognition

if __name__ == '__main__':
    while True:
        tdr = TextDetectionRecognition(['en'])
        tl = Translator('id')

        tdr.load_image(str(input()))
        start = time.time()
        tdr.scan()
        res = tdr.get_result()

        translated = tl.translate(text=tl.convert_to_string(res))
        print(translated)
        print("Exec duration : ", time.time() - start)
        print("Length : ", len(translated))