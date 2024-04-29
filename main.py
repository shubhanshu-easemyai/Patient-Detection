from fastapi import FastAPI
import uvicorn

from core.rdx_connection_handler import connector, logger
from core.source_settings_handler import AppSourceSettingsHandler
from core.general_settings_handler import AppGeneralSettingsHandler
from core.configuration_settings_handler import AppConfigurationSettingsHandler
from core.widget_settings_handler import AppWidgetSettingsHandler
from core.user_session_handler import UserSessionHandler
from core.app_logic_handler import logicHandler
import core.globals as glb
from core.database_handler.models import *


app = FastAPI()


@app.on_event("startup")
async def on_shutdown_event():
    global connector
    connector.run()


@app.on_event("shutdown")
async def on_shutdown_event():
    global connector
    connector.stop()


@connector.consume_events
def fetch_events(data: dict, *args, **kwargs):
    logger.debug(data)
    if data["data"]["task_name"] == "source_group_settings":
        source_settings_handler = AppSourceSettingsHandler()
        source_settings_handler(**data["data"]["func_kwargs"]["data"])
    elif data["data"]["task_name"] == "general_settings":
        general_settings_handler = AppGeneralSettingsHandler()
        general_settings_handler(**data["data"]["func_kwargs"]["data"])
    elif data["data"]["task_name"] == "configuration_settings":
        configuration_settings_handler = AppConfigurationSettingsHandler()
        configuration_settings_handler(**data["data"]["func_kwargs"]["data"])
    elif data["data"]["task_name"] == "widget_settings":
        widget_settings_handler = AppWidgetSettingsHandler()
        widget_settings_handler(**data["data"]["func_kwargs"]["data"])
    elif data["data"]["task_name"] == "user_sessions":
        user_sessions_handler = UserSessionHandler()
        user_sessions_handler(**data["data"]["func_kwargs"]["data"])


@connector.consume_data
def fetch_metadata(data: dict, *args, **kwargs):
    logicHandler.process_data(**data)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, debug=True)
