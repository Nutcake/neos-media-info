import asyncio
import json
import time

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
    current_session.add_media_properties_changed()
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
    last_info = None
    while True:
        try:
            media_info = await get_media_info()
            del media_info["thumbnail"]
        except IOError:
            continue
        if last_info != media_info:
            print("Sending info")
            await websocket.send(json.dumps(media_info, default=str))
            last_info = media_info
        time.sleep(1)
        # TODO: Figure out how the add_media_properties_changed() callback method works and use that instead of busy
        #       waiting


async def main():
    async with websockets.serve(socket_handler, 'localhost', 33442):
        await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
