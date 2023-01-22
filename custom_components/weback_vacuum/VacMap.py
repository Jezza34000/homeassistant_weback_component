import base64
import zlib
import json
import random
import io
import struct

from PIL import Image, ImageDraw, ImageOps

class VacMapDraw:
    
    def __init__(self, vac_map):
        self.vac_map = vac_map
        self.img = self.vac_map.get_map_image()
        self.draw = ImageDraw.Draw(self.img, 'RGBA')

    def draw_charger_point(self, col = (0x1C, 0xE3, 0x78, 0xFF), radius = 10):
        point = self.vac_map.get_charger_point_pixel()
        coords = (point[0] - (radius / 2), point[1] - (radius / 2), point[0] + (radius / 2), point[1] + (radius / 2))
        self.draw.ellipse(coords, col, col)
    
    def draw_robot_position(self, col = (0xDA, 0x36, 0x25, 0xFF), radius = 10):
        point = self.vac_map.get_robot_position_pixel()
        if(point == False):
            return
        coords = (point[0] - (radius / 2), point[1] - (radius / 2), point[0] + (radius / 2), point[1] + (radius / 2))
        self.draw.ellipse(coords, col, col)
    
    def draw_room(self, room):
        self.draw.polygon(self.vac_map._virtual_to_pixel_list(room.get_room_bounds()), tuple(random.choices(range(256), k=4)), (255,255,0,128))

    def draw_rooms(self):
        rooms = self.vac_map.get_rooms()
        for room in rooms:
            self.draw_room(room)

    def draw_path(self, col = (0x1C, 0xE3, 0xDA, 0xFF)):
        path, point_types = self.vac_map.get_path()

        last_coord = None

        for i, coord in enumerate(path):
            if not last_coord:
                last_coord = coord
                continue

            point_type = point_types[i]
            
            self.draw.line((last_coord, coord), col if point_type == VacMap.PATH_VACUUMING else (255,255,255,0), width=3)

            last_coord = coord        

    def get_image(self):
        return self.img

class VacMapRoom:
    def __init__(self, data):
        self.data = data
    def get_clean_times(self):
        return self.data["clean_times"]
    def get_clean_order(self):
        return self.data["clean_order"]
    def get_room_id(self):
        return self.data["room_id"]
    def get_room_name(self):
        if("room_name" in self.data):
            return self.data["room_name"]
        return None
    def get_room_bounds(self, tuple = True):
        r = list()
        for i in range(0, len(self.data["room_point_x"])):
            if(tuple):
                r.append((self.data["room_point_x"][i], self.data["room_point_y"][i]))
            else:
                r.append(list([self.data["room_point_x"][i], self.data["room_point_y"][i]]))
        return r
    def get_room_label_offset(self):
        bounds = self.get_room_bounds()

        min_coord = min(bounds)[0], min(bounds)[1]
        max_coord = max(bounds)[0], max(bounds)[1]

        return min_coord[0] + ((max_coord[0] - min_coord[0]) / 2), min_coord[1] + ((max_coord[1] - min_coord[1]) / 2)

    def get_xaiomi_vacuum_map_card_rooms(self):
        label_offset = self.get_room_label_offset()
        ret = {
            "id": self.get_room_id(),
            "outline": self.get_room_bounds(False),
            "label": { "text": self.get_room_name(), "x": label_offset[0], "y": label_offset[1] }
        }

        return ret

class VacMap:

    MAP_FORMAT_YW_LASER = "yw_ls"
    MAP_FORMAT_YW_VISUAL = "yw_vs"
    MAP_FORMAT_GYRO = "gyro"
    MAP_FORMAT_YW_ES = "yw_es"
    MAP_FORMAT_YW_ES_OLD = "yw_es_old"
    MAP_FORMAT_BV_LASER = "bv_ls"
    MAP_FORMAT_BV_VISUAL = "bv_vs"

    PATH_RELOCATING = 0x40
    PATH_VACUUMING = 0x0

    ALLOW_MAP_FORMATS = { MAP_FORMAT_YW_LASER, MAP_FORMAT_BV_LASER }

    def __init__(self, input):
        self.load_data(input)

    def load_data(self, input):
        self.data = json.loads(zlib.decompress(base64.b64decode(input)))
        self.map_data = bytearray(base64.b64decode(self.data['MapData']))
        self.map_bitmap = False
        self.map_scale = 4
        if("PointData" in self.data):
            self.data["PointData"] = base64.b64decode(self.data['PointData'])
            self.data["PointType"] = base64.b64decode(self.data['PointType'])

    def wss_update(self, input):
        existing_room_data = self.data["room_zone_info"]

        self.load_data(input)

        for i, room in enumerate(self.data["room_zone_info"]):
            existing_room = next(room for room in existing_room_data if room["room_id"] == self.data["room_zone_info"][i]["room_id"])
            self.data["room_zone_info"][i]["room_name"] = existing_room["room_name"]


    def get_map_bitmap(self):
        """Parse MapData into 8-Bit lightness (grayscale) bitmap, return it as bytes"""
        self.map_bitmap = bytearray(b"")
        for i in range(0, len(self.map_data)):
            byte = self.map_data[i]

            self.map_bitmap.append(((byte & 192) >> 6) * 85)
            self.map_bitmap.append(((byte & 48) >> 4) * 85)
            self.map_bitmap.append(((byte & 12) >> 2) * 85)
            self.map_bitmap.append((byte & 3) * 85)

        return self.map_bitmap

    def get_map_image(self, black = (0x1c, 0x89, 0xE3), white = (0xFF, 0xFF, 0xFF)):
        """Get a PIL image of the current map"""
        
        if(not self.map_bitmap):
            self.get_map_bitmap()

        img = Image.frombytes("L", (int(self.data['MapWidth']), int(self.data['MapHigh'])), bytes(self.map_bitmap))
        img = ImageOps.colorize(img, black, white)
        img = img.convert('RGBA')

        img_data = img.getdata()
 
        new_img_data = []
    
        for pixel in img_data:
            if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
                new_img_data.append((255, 255, 255, 0))
            else:
                new_img_data.append(pixel)
    
        img.putdata(new_img_data)
        del new_img_data

        

        img = img.resize((int((self.get_map_width()) * self.map_scale), int((self.get_map_height()) * self.map_scale)), Image.NEAREST)
        return img

    def get_map_width(self):
        return self.data["MapWidth"]

    def get_map_height(self):
        return self.data["MapHigh"]     

    def get_map_resolution(self):
        return self.data["MapResolution"]

    def get_room_id_by_name(self, name):
        return next(room for room in self.data["room_zone_info"] if room["room_name"] == name)["room_id"]

    def get_room_by_id(self, id):
        return VacMapRoom(next(room for room in self.data["room_zone_info"] if room["room_id"] == id))
    
    def get_rooms(self):
        rooms = list()

        for room in self.data["room_zone_info"]:
            rooms.append(VacMapRoom(room))

        return rooms
    
    def get_room_by_name(self, name):
        if(id := self.get_room_id_by_name(name)):
            return self.get_room_by_id(id)
        return None

    def get_charger_point_pixel(self):
        return self._scale_up_pixel_coords(self._pixel_apply_offset((self.data["ChargerPoint"][0], self.data["ChargerPoint"][1])))

    def get_charger_point_virtual(self):
        return self._pixel_to_virtual(self.get_charger_point_pixel())

    def get_robot_position_pixel(self):
        path, point_types = self.get_path()
        if(len(path) > 0):
            return path[len(path) - 1]
        return False
        
    def get_robot_position_virtual(self):
        return self._pixel_to_virtual(self.get_robot_position_pixel())

        
    def get_path(self):
        if "PointData" not in self.data:
            return list(), list()

        point_data = io.BytesIO(self.data["PointData"])
        coords = list()
        point_types = list()

        coords.append(self.get_charger_point_pixel())

        while (x := point_data.read(2)):
            coords.append(self._virtual_to_pixel((struct.unpack('h', x)[0], struct.unpack('h', point_data.read(2))[0])))

        for i, coord in enumerate(coords):
            byte = int(i * 2 / 8)
            bit = int((i * 2 / 8 % 1) * 8)

            if(len(self.data["PointType"]) > byte):
                value = (self.data["PointType"][byte] << bit) & 192
            else:
                value = self.PATH_RELOCATING

            point_types.append(value)

        return coords, point_types

    def _pixel_apply_offset(self, coords):
        """Apply origin offset to (x,y) pixel coordinates"""
        x,y = coords
        return x + self.data["MapOrigin"][0], y + self.data["MapOrigin"][1]

    def _scale_up_pixel_coords(self, coords):
        """Scale coords up by MapResolution"""
        x,y = coords
        return x * self.map_scale, y * self.map_scale

    def _virtual_to_pixel_list(self, coords):
        ret = list()
        for coord in coords:
            ret.append(self._virtual_to_pixel(coord))
        return ret

    def _virtual_to_pixel(self, coords):
        """Convert virtual (laser map coordinates) to pixel coords, taking origin into account"""
        x, y = coords
        x, y = round((self.data['MapOrigin'][0] + (x * 2 * self.get_map_resolution())) * self.map_scale), round((self.data['MapOrigin'][1] + (y * 2 * self.get_map_resolution())) * self.map_scale)
        return x , y

    def _pixel_to_virtual(self, coords):
        x, y = coords
        x, y = x / self.map_scale, y / self.map_scale
        x, y = (x - self.data["MapOrigin"][0]) / self.get_map_resolution() / 2, (y - self.data["MapOrigin"][1]) / self.get_map_resolution() / 2
        return x, y

    def calibration_points(self):
        cal = list()

        map_point = self._virtual_to_pixel((0,0))
        cal.append({
                "vacuum": {"x": 0, "y": 0},
                "map": {"x": int(map_point[0]), "y": int(map_point[1])}
        })

        map_point = self._virtual_to_pixel((self.get_map_width(),self.get_map_height()))
        cal.append({
                "vacuum": {"x": self.get_map_width(), "y": self.get_map_height()},
                "map": {"x": int(map_point[0]), "y": int(map_point[1])}
        })

        map_point = self._virtual_to_pixel((0,self.get_map_height()))
        cal.append({
                "vacuum": {"x": 0, "y": self.get_map_height()},
                "map": {"x": int(map_point[0]), "y": int(map_point[1])}
        })
        
        map_point = self._virtual_to_pixel((self.get_map_width(), 0))
        cal.append({
                "vacuum": {"x": self.get_map_width(), "y": 0},
                "map": {"x": int(map_point[0]), "y": int(map_point[1])}
        })

        return cal

    def get_predefined_selections(self):
        all_rooms = self.get_rooms()
        predefined_selections = list()

        for room in all_rooms:
            predefined_selections.append(room.get_xaiomi_vacuum_map_card_rooms())

        return predefined_selections