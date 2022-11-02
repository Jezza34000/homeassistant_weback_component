# Weback/Tesvor component for HomeAssistant

[![](https://img.shields.io/github/release/Jezza34000/homeassistant_weback_component/all.svg?style=for-the-badge)](https://github.com/Jezza34000/homeassistant_weback_component)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Home Assistant component for controling robot from brand like : Neatsvor / Tesvor / Orfeld / Abir...
Who using WeBack or Tesvor apps.

## Installation

Go to Home Assistant > HACS > Integrations > Click on tree dot (on top right corner) > Custom repositories \
and fill :
* **Repository** :  `Jezza34000/homeassistant_weback_component`
* **Category** : `Integration`

Click on ADD

## Configuration

Edit your Home Assistant `configuration.yaml` and set :

``` YAML
weback_vacuum:
  username: <your WeBack/Tesvor email, required>
  password: <your WeBack/Tesvor password, required>
  region: <your country phone code e.g. for france code is 33, required>
  application: <configuration app, optionnal>
  client_id: <api client, optionnal>
  api_version: <api version used, optionnal> 
  language : <language code 2 chars, optionnal>
```

**username** : Login used to setup your robot application. \
**password** : password.\
**region** : code can be found here : https://en.wikipedia.org/wiki/List_of_country_calling_codes **provide only digit number. Do not insert leading "+"** \
**application** : if you use "WeBack" do not try to change this field.  \
**client_id**, **api_version**, **language**: seems to have no effect. Do not use it.


Once set you can restart Home Assitant.
