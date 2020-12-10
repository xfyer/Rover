### OSX

* Python 3.9+ Is Required

```bash
sudo port install python39 py39-pip py39-setuptools py39-setuptools py39-psycopg2 openssl freetype
# sudo port install py39-numpy # (OR) brew install openblas

sudo port select --set python3 python39
sudo port select --set pip3 pip39

# Instructions For Variables
# https://stackoverflow.com/a/65072442/6828099
# https://stackoverflow.com/a/60748789/6828099

export PATH=/opt/local/lib/postgresql13/bin/:$PATH
export LDFLAGS="-L/opt/local/lib"
export CPPFLAGS="-I/opt/local/include"

# You may need to specify --no-cache-dir after install
pip3 install -r requirements.txt
```

### RPi

```bash
sudo apt-get install libfreetype6-dev libopenjp2-7 libtiff5

# You may need to specify --no-cache-dir after install
pip3 install -r requirements.txt
```