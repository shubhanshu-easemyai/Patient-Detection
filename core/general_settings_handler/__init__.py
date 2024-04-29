from typing import Any
import importlib

from core.rdx_connection_handler import *
from core.database_handler.models import *
from core.general_settings_handler import tabs_handler
import core.globals as glb


class AppGeneralSettingsHandler:
    def __init__(self) -> None:
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        func_name = "{}_general_settings".format(kwds["type"])
        if hasattr(self, func_name) and callable(func := getattr(self, func_name)):
            try:
                func(**kwds)
            except Exception as e:
                logger.debug(e)

    def send_data_to_server(self, session_id, task_name, data):
        connector.produce_data(
            message={
                "task_name": task_name,
                "func_kwargs": {
                    "session_id": session_id,
                    **data,
                },
            },
            destination="socket_server",
            event_type="general_setting",
        )

    def get_general_settings(self, session_id, tab_name, user_data, **kwds):
        try:
            response = {}
            user_details = UserInfo.objects(**user_data).get()

            tabs_handler_func = getattr(tabs_handler, "get_{}".format(tab_name))
            response = tabs_handler_func(user_details)

            self.send_data_to_server(
                session_id=session_id,
                task_name="get",
                data=response,
            )
        except Exception as e:
            logger.debug(e)

    def post_general_settings(self, session_id, tab_name, settings, user_data, **kwds):
        try:
            try:
                user_details = UserInfo.objects(**user_data).get()
            except DoesNotExist:
                user_details = UserInfo(**user_data)
                user_details.save()

            tabs_handler_func = getattr(tabs_handler, "post_{}".format(tab_name))
            response = tabs_handler_func(settings, user_details)

            self.send_data_to_server(
                session_id=session_id,
                task_name="post",
                data=response,
            )
        except Exception as e:
            logger.debug(e)

    def reset_general_settings(self, session_id, tab_name, user_data, **kwds):
        try:
            user_details = UserInfo.objects(**user_data).get()

            tabs_handler_func = getattr(tabs_handler, "reset_{}".format(tab_name))
            response = tabs_handler_func(user_details)

            self.send_data_to_server(
                session_id=session_id,
                task_name="reset",
                data=response,
            )
        except Exception as e:
            logger.debug(e)
