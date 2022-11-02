# Weback/Tesvor component for HomeAssistant

Home Assistant component for controling robot from brand like : Neatsvor / Tesvor / Orfeld / Abir / ...
Who using WeBack or Tesvor apps.

## Installation

Copy this repository inside your `custom_components` Home Assistant's folder

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
