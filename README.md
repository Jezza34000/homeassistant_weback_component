# WeBack component for HomeAssistant

[![](https://img.shields.io/github/release/Jezza34000/homeassistant_weback_component/all.svg?style=for-the-badge)](https://github.com/Jezza34000/homeassistant_weback_component)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)\
Home Assistant component for controlling robot from brand like : Neatsvor / Tesvor / Orfeld / Abir...
This component can control robot using WeBack app.

> Please note that several of these robot brands also use the Tuya/Smartlife platform in parallel (depending on the model). If your robot works with Tuya/Smartlife this integration will not be compatible.

> This integration is not compatible with Tesvor robot models that use the “TESVOR HOME” application

## Installation (with HACS)

1. Got to HACS
2. Integrations
3. EXPLORE & DOWNLOAD REPOSITORIES
4. Enter "Weback"
5. DOWNLOAD THIS REPOSITORY

## Installation (manual)

1. Download last release.
2. Unzip `weback_component` folder into your HomeAssistant : `custom_components`
3. Restart HA

## Configuration

Edit your Home Assistant `configuration.yaml` and set :

``` YAML
weback_vacuum:
  username: <your WeBack email, required>
  password: <your WeBack password, required>
  region: <your country phone code e.g. for france code is 33, required>
  application: <configuration app, optional>
  client_id: <api client, optional>
  api_version: <api version used, optional>
  language : <language code 2 chars, optional>
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


## Maps and Rooms

>  Maps are supported for LIDAR vacuum only.

Tested on:
  - Electriq "Helga" iQlean-LR01

Integration with [PiotrMachowski/lovelace-xiaomi-vacuum-map-card](https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card) supports automatic map calibration and room boundaries.

The vacuum entity has been modified to accept `send_command`s for room / segment cleaning.

### Example `lovelace-xiaomi-vacuum-map-card` card setup

To support automatic room boundaries, the Lovelace card needs to be templated. An example of this using [iantrich/config-template-card](https://github.com/iantrich/config-template-card)

*Please set both vacuum and camera entities appropriately. `camera.robot_map` and `vacuum.robot` in this example*


``` YAML
type: custom:config-template-card
variables:
  ROOMS: states['camera.robot_map'].attributes.rooms
entities:
  - camera.robot_map
card:
  type: custom:xiaomi-vacuum-map-card
  map_source:
    camera: camera.robot_map
  calibration_source:
    camera: true
  entity: vacuum.robot
  vacuum_platform: send_command
  title: Vacuum
  preset_name: Live map
  map_modes:
    - template: vacuum_clean_zone
    - template: vacuum_clean_segment
      name: Rooms
      icon: mdi:floor-plan
      predefined_selections: ${ROOMS}

```

## Issues

If you find any bug or you're experiencing any problem, please set your Home Assistant log level to debug before opening any issues. And provide full log.
To set your HA into debug level copy this into your `configuration.yaml` :

``` YAML
logger:
   default: error
   logs:
     custom_components.weback_vacuum: debug
```
