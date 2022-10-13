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
  region: <your country phone code e.g. for france the code is 33, required>
  language : <language code 2 chars, optionnal>
  application: <configuration app, optionnal>
  client_id: <api client, optionnal>
  api_version: <api version used, optionnal> 
```

Once set you can restart Home Assitant.
