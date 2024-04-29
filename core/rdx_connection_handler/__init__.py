from rdx import Connector, console_logger

connector = Connector(connection_type="kafka")

service_details = connector.app_settings()
logger = console_logger.setup_logger(name=service_details["SERVICE_NAME"])

import mongoengine

mongoengine.connect(
    host="mongodb://{}:{}@{}:{}/{}?authSource={}".format(
        service_details["SERVICE_SETTINGS"]["DATABASE_USERNAME"],
        service_details["SERVICE_SETTINGS"]["DATABASE_PASSWORD"],
        service_details["SERVICE_SETTINGS"]["DATABASE_HOST"],
        service_details["SERVICE_SETTINGS"]["DATABASE_PORT"],
        service_details["SERVICE_SETTINGS"]["DATABASE_NAME"],
        service_details["SERVICE_SETTINGS"]["DATABASE_NAME"],
    ),
)
