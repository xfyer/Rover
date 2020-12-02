### OSX

```bash
sudo port install python38 py38-setuptools py38-setuptools py38-psycopg2 openssl freetype

# Instructions For Variables
# https://stackoverflow.com/a/65072442/6828099
# https://stackoverflow.com/a/60748789/6828099

export PATH=/opt/local/lib/postgresql13/bin/:$PATH
export LDFLAGS="-L/opt/local/lib"
export CPPFLAGS="-I/opt/local/include"

# You may need to specify --no-cache-dir after install
pi3 install -r requirements.txt
```

### RPi

```bash
sudo apt-get install libfreetype6-dev libopenjp2-7 libtiff5

# You may need to specify --no-cache-dir after install
pip3 install -r requirements.txt
```