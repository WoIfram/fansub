# adcut
По данному файлу субтитров, тайминг которого соответствует немусорным отрывкам видео, и видеофайлу, генерирует новый видеофайл, из которого выкинуты все мусорные отрывки.
Чтобы это работало, необходимо, чтобы `ffmpeg` был прописан в PATH, либо же надо передать путь к бинарнику `ffmpeg` аргументом `--ffmpeg-path`.
По дефолту в `ffmpeg`, помимо необходимых аргументов, передаются также `-y` и `-strict -2`. У скриптика есть помощь, вызывающаяся по `./adcut.py -h`.
Скрипт работает только в Python 3.5+.
Пример команды (запускать из корневой директории репозитория):

```./adcut.py ~/Downloads/s07e19_raw.mp4 pieces.ass -o s07e19.mp4```

Сгенерирует нормальный рип в репозитории с именем `s07e19.mp4`.
