from typing import Any

from core.utils import *
import core.globals as glb
from core.widget_settings_handler import AppWidgetSettingsHandler
from core.database_handler.models import *
from core.rdx_connection_handler import logger


class UserSessionHandler:
    def __init__(self) -> None:
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        func_name = "{}".format(kwds["type"])
        if hasattr(self, func_name) and callable(func := getattr(self, func_name)):
            try:
                func(**kwds)
            except Exception as e:
                logger.debug(e)

    def activate_session(
        self, session_id, user_data, widgets=[], timezone="Asia/Kolkata", **kwargs
    ):
        try:
            user_data = UserInfo.objects.get(user_id=user_data["user_id"])
            for index in range(len(widgets)):
                try:
                    user_session_object = UserSessions.objects.get(
                        user_data=user_data, timezone=timezone, **widgets[index]
                    )
                except DoesNotExist:
                    user_session_object = UserSessions(
                        user_data=user_data, timezone=timezone, **widgets[index]
                    )
                    user_session_object.save()

                widgets[index].update(**user_session_object.payload())

            if user_data["user_id"] not in glb.user_sessions:
                glb.user_sessions.update({user_data["user_id"]: {session_id: widgets}})
            else:
                glb.user_sessions[user_data["user_id"]].update({session_id: widgets})
            widget_settings_handler = AppWidgetSettingsHandler()
            widget_settings_handler.send_widget_data()
        except Exception:
            pass
        logger.debug(glb.user_sessions)

    def deactivate_session(self, session_id, user_data, **kwargs):
        try:
            # logger.debug(glb.user_sessions)
            user_data = UserInfo.objects.get(user_id=user_data["user_id"])
            if user_data["user_id"] in glb.user_sessions:
                if session_id in glb.user_sessions[user_data["user_id"]]:
                    del glb.user_sessions[user_data["user_id"]][session_id]
            widget_settings_handler = AppWidgetSettingsHandler()
            widget_settings_handler.send_widget_data()
        except Exception:
            pass
