# data over audio

experiments

## requirements

* ruby + bundler
* python < 3 + pip
* portaudio
* OSX

## setup

```
bundle install
```

```
brew install portaudio
pip install -r requirements.txt
```

turn off ambient noise reduction on OSX

![](http://content.screencast.com/users/pewniak747/folders/Jing/media/915056b9-f8fc-4234-9782-8c78fe971557/00000119.png)

## running

start listener:

```
python listen.py
```

start emitter:

```
ruby sound.rb < data.txt
```
