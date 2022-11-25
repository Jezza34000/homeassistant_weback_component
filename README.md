# Weback/Tesvor component for HomeAssistant

[![](https://img.shields.io/github/release/Jezza34000/homeassistant_weback_component/all.svg?style=for-the-badge)](https://github.com/Jezza34000/homeassistant_weback_component)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Home Assistant component for controlling robot from brand like : Neatsvor / Tesvor / Orfeld / Abir...
Who using WeBack or Tesvor apps.

## Installation

Go to Home Assistant > HACS > Integrations > Click on tree dot (on top right corner) > Custom repositories \
and fill :
* **Repository** :  `Jezza34000/homeassistant_weback_component`
* **Category** : `Integration`

Click on `ADD`, restart HA.

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

Config example :

``` YAML
weback_vacuum:
  username: mymail@contactme.com
  password: mysupersecuredpassword
  region: 33
```

> Do not use any leading/ending characters like < > " ' + 

Once configuration set you can restart Home Assistant.
After restart, a new vacuum entity is created with the name defined into WeBack apps.


## Important : API change since 2022

If you have bought and create your robot account prior to 2022 it's possible you are still registered on the old API system, and you account will have problem or not work. \
if you concerned, to ensure proper working, please follow thoses steps: \
Go to WeBack app :
* Remove you robot from account
* Logout from account
* Remove your account
* Create a new account
* Add your robot to your new account


## Issues

If you find any bug or you're experiencing any problem, please set your Home Assistant log level to debug before opening any issues. And provide full log.
To set your HA into debug level copy this into your `configuration.yaml` :

``` YAML
logger:
   default: error
   logs:
     custom_components.weback_vacuum: debug
```



