import asyncio
import json
import time
import argparse

import websockets

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager, GlobalSystemMediaTransportControlsSession, \
    MediaPropertiesChangedEventArgs


async def get_media_info():
    sessions = await MediaManager.request_async()

    # This source_app_user_model_id check and if statement is optional
    # Use it if you want to only get a certain player/program's media
    # (e.g. only chrome.exe's media not any other program's).

    # To get the ID, use a breakpoint() to run sessions.get_current_session()
    # while the media you want to get is playing.
    # Then set TARGET_ID to the string this call returns.

    current_session = sessions.get_current_session()
    if current_session:  # there needs to be a media session running
        info = await current_session.try_get_media_properties_async()

        # song_attr[0] != '_' ignores system attributes
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info)
                     if not song_attr.startswith("_")}

        # converts winrt vector to list
        info_dict['genres'] = list(info_dict['genres'])

        return info_dict

    # It could be possible to select a program from a list of current
    # available ones. I just haven't implemented this here for my use case.
    # See references for more information.
    raise IOError('No running media session')


async def socket_handler(websocket: websockets.WebSocketServerProtocol):
    print("Connected")
    delim = ";"

    def esc(s: str):
        return s.replace(delim, ',')

    last_info = None
    while True:
        try:
            media_info = await get_media_info()
            del media_info["thumbnail"]
        except IOError:
            media_info = None
        if last_info != media_info:
            print("Sending info")
            await websocket.send(f"{esc(media_info['artist'])}{delim}{esc(media_info['title'])}{delim}"
                                 f"{esc(media_info['album_artist'])}{delim}{esc(media_info['album_title'])}")
            last_info = media_info
        time.sleep(1)
        # TODO: Figure out how the add_media_properties_changed() callback method works and use that instead of busy
        #       waiting


async def main(port, addr):
    async with websockets.serve(socket_handler, addr, port):
        await asyncio.Future()


if __name__ == '__main__':
    aparse = argparse.ArgumentParser(description="Send current Windows media information to websocket client.")
    aparse.add_argument("-p", "--port", help="port to bind to", type=int, default=33442)
    aparse.add_argument("-a", "--addr", help="address to bind to", type=str, default="localhost")
    args = aparse.parse_args()
    asyncio.run(main(port=args.port, addr=args.addr))
