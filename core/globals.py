from apscheduler.schedulers.background import BackgroundScheduler
from core.rdx_connection_handler import logger
import datetime
import queue

from core.widget_settings_handler import AppWidgetSettingsHandler

user_sessions = {}
update_widget_interval = 10


sources_list = []
polygons = []
loaded_camera_ids = {}
max_time_threshold = 0 #default is set to 1
object_class_name = "person"
# max_time_threshold = 10
# last_alert_generated = datetime.datetime.utcnow()
# confidence_threshold = {"person": 0.7, "helmet": 0.5, "safety_vest": 0.5, "head": 0.5}
# padding = 20
message_queue = queue.Queue(maxsize=1000)
# iot_command_queue = queue.Queue(maxsize=1000)
# include_head = False
# iot_server_url = "http://192.168.1.121/api/v1/iot/device-publish"
# enable_voice_command = False

# user_sessions = {}
sample_generator = {}


def job():
    widget_settings_handler = AppWidgetSettingsHandler()
    widget_settings_handler.send_widget_data()
    # logger.info("job() is called")
    # logger.debug(user_sessions)


scheduler = BackgroundScheduler(**{"timezone": "utc"})
scheduler.add_job(job, "interval", seconds=update_widget_interval, id="interval_task")
scheduler.start()


def update_job(interval):
    global scheduler, max_time_threshold
    max_time_threshold = int(interval)
    scheduler.reschedule_job(
        job_id="interval_task", trigger="interval", **{"seconds": max_time_threshold}
    )


