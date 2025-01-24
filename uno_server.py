# -*- coding: utf-8 -*-
# @Author: Anthony
# @Date:   2016-03-30 12:48:58
# @Last Modified by:   Anthony
# @Last Modified time: 2016-04-11 11:59:55

import os
import sys
import json
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
from configs.config import configs
from room import rooms
import websocket
# import keyboard

# Ensure necessary directories exist
if not os.path.exists('logs'):
    os.makedirs('logs')

class BaseHandler(tornado.web.RequestHandler):
    def redirect_param(self, url, **params):
        if params:
            query = "&".join([f"{k}={v}" for k, v in params.items()])
            self.redirect(f"{url}?{query}")
        else:
            self.redirect(url)

class BaseRoomHandler(BaseHandler):
    def get_room(self, room_name, player_name=None):
        if not rooms.has_room(room_name):
            params = {"room": room_name, "msg": "room_not_exist"}
            if player_name:
                params["player"] = player_name
            self.redirect_param('/create', **params)
            return None
        return rooms.get_room(room_name)

class LobbyHandler(BaseHandler):
    def get(self):
        self.render('lobby.html', rooms=rooms)

class CreateHandler(BaseHandler):
    def get(self, room_name=None):
        if room_name is None:
            self.render('create.html')
        elif rooms.has_room(room_name):
            self.redirect_param(f'/room/{room_name}', msg='room_already_exist')
        else:
            r = rooms.create_room(room_name)
            if r:
                self.redirect_param(f'/room/{room_name}')
            else:
                self.redirect_param('/', room=room_name, error=str(r))

class RoomHandler(BaseRoomHandler):
    def get(self, room_name):
        room = self.get_room(room_name)
        if room:
            self.render('join.html', room=room)

class OptionsHandler(BaseRoomHandler):
    def get(self, room_name):
        room = self.get_room(room_name)
        if room:
            self.render('options.html', room=room)

class RoomCloseHandler(BaseRoomHandler):
    def get(self, room_name):
        if rooms.close_room(room_name):
            self.redirect_param('/', msg='room_close_successful')
        else:
            self.redirect_param('/', msg='room_close_failed')

class RoomRestartHandler(BaseRoomHandler):
    def get(self, room_name):
        room = self.get_room(room_name)
        if room:
            room.shutdown()
            self.redirect(f'/room/{room_name}')

class RoomClearHandler(BaseRoomHandler):
    def get(self, room_name):
        room = self.get_room(room_name)
        if room:
            room.clear_scoreboard()
            self.redirect(f'/room/{room_name}')

class PlayerHandler(BaseRoomHandler):
    def get(self, room_name, player_name):
        room = self.get_room(room_name)
        if room:
            player = room.join(player_name)
            if player:
                self.render('table.html', room=room, player=player, chat_root=configs.chat_root)
            else:
                self.redirect_param(f'/room/{room_name}', msg=str(player))

class NotFoundHandler(BaseHandler):
    def get(self):
        self.render('404.html')

# Tornado application setup
handlers = [
    (r'/', LobbyHandler),
    (r'/create', CreateHandler),
    (r'/create/(\w+)', CreateHandler),
    (r'/room/(\w+)', RoomHandler),
    (r'/room/(\w+)/options', OptionsHandler),
    (r'/room/(\w+)/close', RoomCloseHandler),
    (r'/room/(\w+)/restart', RoomRestartHandler),
    (r'/room/(\w+)/clear', RoomClearHandler),
    (r'/room/(\w+)/player/(\w+)', PlayerHandler),
    (r'/room/(\w+)/player/(\w+)/ws', websocket.ws_player),
    (r'.*', NotFoundHandler),
]

app = tornado.web.Application(
    handlers=handlers,
    template_path='template',
    static_path='static',
    debug=True
)

# Start server
if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(int(os.environ.get("PORT", 8888)), address="0.0.0.0")

    # print(f"Server started on port {configs.port}")
    # print("Press 'q' to exit.")

    # def check_exit():
    #     if keyboard.is_pressed('q'):
    #         print("'q' pressed. Exiting...")
    #         tornado.ioloop.IOLoop.current().stop()
    #         sys.exit(0)

    tornado.ioloop.PeriodicCallback(check_exit, 100).start()
    tornado.ioloop.IOLoop.current().start()
