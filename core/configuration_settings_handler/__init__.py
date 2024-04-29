from typing import Any

from core.utils import *
from core.configuration_settings_handler import tabs_handler
from core.rdx_connection_handler import connector, logger
from core.database_handler.models import *


class AppConfigurationSettingsHandler:
    def __init__(self) -> None:
        self.connector = connector

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        func_name = "{}_configuration_settings".format(kwds["type"])
        if hasattr(self, func_name) and callable(func := getattr(self, func_name)):
            try:
                func(**kwds)
            except Exception as e:
                logger.error(
                "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
            )
                
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
            event_type="configuration_settings",
        )

    def get_configuration_settings(
        self, session_id, tab_name, user_data, source_details, **kwds
    ):
        try:
            logger.debug(source_details)
            source_info = SourceInfo.objects(**source_details).get()
            user_details = UserInfo.objects(**user_data).get()

            tabs_handler_func = getattr(tabs_handler, "get_{}".format(tab_name))
            response = tabs_handler_func(source_info, user_details)
            logger.debug(response)

            load_configuration_settings(**source_info.payload())
            self.send_data_to_server(
                session_id=session_id,
                task_name="get",
                data=response,
            )
        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )

    def post_configuration_settings(
        self, session_id, tab_name, settings, user_data, source_details, **kwds
    ):
        try:
            source_info = SourceInfo.objects(**source_details).get()
            user_details = UserInfo.objects(**user_data).get()

            tabs_handler_func = getattr(tabs_handler, "post_{}".format(tab_name))
            response = tabs_handler_func(settings, source_info, user_details)
            logger.debug(response)

            load_configuration_settings(**source_info.payload())
            self.send_data_to_server(
                session_id=session_id,
                task_name="post",
                data=response,
            )

        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )
            
    def reset_configuration_settings(
        self, session_id, tab_name, user_data, source_details, **kwds
    ):
        try:
            source_info = SourceInfo.objects(**source_details).get()
            user_details = UserInfo.objects(**user_data).get()
            tabs_handler_func = getattr(tabs_handler, "reset_{}".format(tab_name))
            response = tabs_handler_func(source_info, user_details)

            load_configuration_settings(**source_info.payload())
            self.send_data_to_server(
                session_id=session_id,
                task_name="reset",
                data=response,
            )
            
        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )