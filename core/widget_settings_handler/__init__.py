import datetime
import pytz

from typing import Any
import json

from core.utils import *
from core.database_handler.models import *
import core.globals as glb
from core.rdx_connection_handler import logger, service_details


class AppWidgetSettingsHandler:
    def __init__(self) -> None:
        self.service_name = service_details["SERVICE_NAME"]

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        func_name = "{}_{}".format(kwds["type"], kwds["tab_name"])
        if hasattr(self, func_name) and callable(func := getattr(self, func_name)):
            try:
                func(**kwds)
            except Exception as e:
                logger.debug(e)

    def update_widget_cache(
        self, user_id, session_id, widget_id, index, params, payload, **kwargs
    ):
        try:
            glb.user_sessions[user_id][session_id][index]["widget_data"] = (
                copy.deepcopy(payload)
            )
            glb.user_sessions[user_id][session_id][index]["user_inputs"] = (
                copy.deepcopy(params)
            )

            user_data = UserInfo.objects.get(user_id=user_id)

            user_session_object = UserSessions.objects.get(
                user_data=user_data, widget_id=widget_id
            )
            user_session_object.user_inputs = params
            user_session_object.widget_dat = payload
            user_session_object.last_updated = datetime.datetime.utcnow()
            user_session_object.save()
        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )
        return

    def filter_camera_name_dropdown(
        self, widget_id, session_id, user_data=None, **kwargs
    ):
        if isinstance(user_data, dict):
            user_id = user_data["user_id"]
        else:
            user_id = kwargs["user_id"]
        pipeline = [
            {"$match": {"source_details.source_owner": user_id}},
            {
                "$group": {
                    "_id": None,
                    "source_names": {"$addToSet": "$source_details.source_name"},
                }
            },
        ]

        result = DetectionLogs.objects.aggregate(pipeline)
        for data in result:
            response = []
            for group in data["source_names"]:
                response.append({"label": group, "value": group})

            connector.produce_data(
                message={
                    "task_name": "widget_settings",
                    "func_kwargs": {
                        "type": "filter",
                        "session_id": session_id,
                        "widget_id": widget_id,
                        "camera_name_dropdown": response,
                    },
                },
                destination="socket_server",
                event_type="widget_settings",
            )
            return


    # def get_live_alerts(
    #     self,
    #     user_data=None,
    #     params={}, 
    #     widget_id="6602aaea005263fb79b1094a", 
    #     **kwargs):
    #     try:
    #         pass
    #         # logger.debug("user_data: %s", user_data)
    #         # logger.debug("kwargs: %s", params)
    #         # logger.debug("widget_id: %s", widget_id)
    #         # logger.debug("user_id: %s", kwargs["user_id"])
    #         # logger.debug("session_id: %s", kwargs["session_id"])
    #         # logger.debug("index: %s", kwargs["index"])
    #         # logger.debug("widget_name: %s", kwargs["widget_name"])
    #         # logger.debug("widget_data: %s", kwargs["widget_data"])
    #         # logger.debug("timezone: %s", kwargs["timezone"])
    #         # logger.debug("last_updated: %s", kwargs["last_updated"])

    #         session_id = kwargs["session_id"] if "session_id" in kwargs else None

    #         if isinstance(user_data, dict):
    #             user_id = user_data["user_id"]
    #             logger.debug(user_id)
    #         else:
    #             user_id = kwargs["user_id"]
    #             logger.debug(user_id)

    #         if "index" not in kwargs:
    #             for index, widget in enumerate(glb.user_sessions[user_id][session_id]):
    #                 if widget["widget_id"] == widget_id:
    #                     kwargs["index"] = index
    #                     break

    #         index = kwargs.pop("index")

    #         pipeline = [
    #             {
    #                 "$match": {
    #                     "source_details.source_owner": user_id,
    #                 },
    #             },
    #             {
    #                 "$sort": {
    #                     "created": -1,
    #                 },
    #             },
    #             {"$limit": 100},
    #         ]
            
    #         if any(params):
    #             if "filter" in params and params["filter"]:
    #                 pipeline[0]["$match"].update(
    #                     {
    #                         "$expr": {
    #                             "$setIsSubset": [
    #                                 ["$source_details.source_name"],
    #                                 params["filter"],
    #                             ]
    #                         }
    #                     }
    #                 )
    #         elif "user_inputs" in  glb.user_sessions[user_id][session_id][index]:
    #             params = copy.deepcopy(
    #                 glb.user_sessions[user_id][session_id][index]["user_inputs"]
    #             )

    #         response = []

    #         # for log in DetectionLogs.objects.aggregate(pipeline):
    #         #     created_datetime = log["created"]

    #         #     logger.debug(created_datetime)
                
    #         #     # Convert UTC time to IST
    #         #     # ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    #         #     # ist_timezone_str = str(ist_timezone)
    #         #     # logger.debug(ist_timezone)
    #         #     # logger.debug(ist_timezone_str)


    #         #     created_datetime_str = str(created_datetime)
                
    #         #     date_part, time_part = created_datetime_str.split(" ")
    #         #     # Split the time part at the '.' character and take only the first part
    #         #     time_part = time_part.split(".")[0]

    #         #     logger.debug(date_part)
    #         #     logger.debug(time_part)

    #         #     _data = {
    #         #         "images": ["/static_server/app_media/{}/Media/{}".format(
    #         #                     self.service_name, log["image_url"]
    #         #                 )],
    #         #         "camera": log["source_details"]["source_name"],
    #         #         "alert": log["area"],
    #         #         "priority": "high",
    #         #         "date": date_part,
    #         #         "time": time_part,
    #         #     }
    #         #     response.append(_data)

    #         IST = pytz.timezone('Asia/Kolkata')

    #         for log in DetectionLogs.objects.aggregate(pipeline):
    #             created_datetime = log["created"]
    #             vanished_datetime = log["vanished"]

    #             # Convert UTC time to IST
    #             created_datetime_ist = created_datetime.astimezone(IST)
    #             vanished_datetime_ist = vanished_datetime.astimezone(IST)

    #             # logger.debug(created_datetime_ist)

    #             created_datetime_ist_str = created_datetime_ist.strftime("%Y-%m-%d %H:%M:%S")
    #             vanished_datetime_ist_str = vanished_datetime_ist.strftime("%Y-%m-%d %H:%M:%S")

    #             date_part_created, time_part_created = created_datetime_ist_str.split(" ")
    #             date_part_vanished, time_part_vanished = vanished_datetime_ist_str.split(" ")

    #             logger.debug(created_datetime)
    #             logger.debug(date_part_created)
    #             logger.debug(time_part_created)

    #             logger.debug(vanished_datetime)
    #             logger.debug(date_part_vanished)
    #             logger.debug(time_part_vanished)

    #             _data = {
    #                 "images": ["/static_server/app_media/{}/Media/{}".format(
    #                             self.service_name, log["image_url"]
    #                         )],
    #                 "camera": log["source_details"]["source_name"],
    #                 "alert": log["area"],
    #                 "date": date_part_created,
    #                 "created time": time_part_created,
    #                 "vanished time": time_part_vanished,
    #             }
    #             response.append(_data)

    #         # logger.debug(response)

    #         message = {
    #             "task_name": "widget_settings",
    #             "func_kwargs": {
    #                 "session_id": session_id,
    #                 "widget_id": widget_id,
    #                 "type": "get",
    #                 "data": {
    #                     "live_alerts": {
    #                         "alert_table": {
    #                             "data": {
    #                                 "labels": [
    #                                     "images",
    #                                     "camera",
    #                                     "alert",
    #                                     "date",
    #                                     "created time",
    #                                     "vanished time",
    #                                 ],
    #                                 "datasets": response,
    #                                 "total": 1,
    #                             }
    #                         }
    #                     },
    #                     **params,
    #                 },
    #             },
    #         }

    #         # logger.debug(params)

    #         # logger.debug(message)

    #         connector.produce_data(
    #             message=message,
    #             destination="socket_server",
    #             event_type="widget_settings",
    #         )
    #     except Exception as e:
    #         logger.error(
    #         "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
    #     )
    #     finally:
    #         self.update_widget_cache(
    #             user_id, session_id, widget_id, index, params, message
    #         )
    #     return

    def get_live_alerts(
        self,
        user_data=None,
        params={}, 
        widget_id="6602aaea005263fb79b1094a", 
        **kwargs):
        try:
            session_id = kwargs["session_id"] if "session_id" in kwargs else None

            if isinstance(user_data, dict):
                user_id = user_data["user_id"]
                logger.debug(user_id)
            else:
                user_id = kwargs["user_id"]
                logger.debug(user_id)

            if "index" not in kwargs:
                for index, widget in enumerate(glb.user_sessions[user_id][session_id]):
                    if widget["widget_id"] == widget_id:
                        kwargs["index"] = index
                        break

            index = kwargs.pop("index")

            pipeline = [
                {
                    "$match": {
                        "source_details.source_owner": user_id,
                    },
                },
                {
                    "$sort": {
                        "created": -1,
                    },
                },
                {"$limit": 100},
            ]
            
            if any(params):
                if "filter" in params and params["filter"]:
                    pipeline[0]["$match"].update(
                        {
                            "$expr": {
                                "$setIsSubset": [
                                    ["$source_details.source_name"],
                                    params["filter"],
                                ]
                            }
                        }
                    )
            elif "user_inputs" in  glb.user_sessions[user_id][session_id][index]:
                params = copy.deepcopy(
                    glb.user_sessions[user_id][session_id][index]["user_inputs"]
                )

            response = []

            # IST = pytz.timezone('Asia/Kolkata')

            for log in DetectionLogs.objects.aggregate(pipeline):
                vanished_datetime = log["vanished"]
                logger.debug(vanished_datetime)

                if vanished_datetime != None:
                    created_datetime_str = log["created"].strftime("%Y-%m-%d %H:%M:%S")
                    time_part_created = created_datetime_str.split(" ")[1]

                    vanished_datetime_str = vanished_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    date_part_vanished, time_part_vanished = vanished_datetime_str.split(" ")

                    # logger.debug(created_datetime_str)
                    # logger.debug(vanished_datetime_str)
                    # logger.debug(time_part_created)
                    # logger.debug(date_part_vanished)
                    # logger.debug(time_part_vanished)

                            # "images": "/static_server/app_media/{}/Media/{}".format(
                            #     self.service_name, log["image_url"]
                            # ),

                    logger.debug(["/static_server/app_media/{}/Media/{}".format(
                                self.service_name, log["image_url"]
                            ),])
                    _data = {
                            "media_link": ["/static_server/app_media/{}/Media/{}".format(
                                self.service_name, log["image_url"]
                            ),],
                            "camera": log["source_details"]["source_name"],
                            "alert": log["roi_name"],
                            "date": date_part_vanished,
                            "created time": time_part_created,
                            "vanished time": time_part_vanished,
                        }
                    response.append(_data)

                # created_datetime = log["created"]
                # vanished_datetime = log["vanished"]

                # if created_datetime is None or vanished_datetime is None:
                #     # Convert UTC time to IST
                #     created_datetime_ist = created_datetime.astimezone(IST)
                #     vanished_datetime_ist = vanished_datetime.astimezone(IST)

                #     # logger.debug(created_datetime_ist)

                #     created_datetime_ist_str = created_datetime_ist.strftime("%Y-%m-%d %H:%M:%S")
                #     vanished_datetime_ist_str = vanished_datetime_ist.strftime("%Y-%m-%d %H:%M:%S")

                #     time_part_created = created_datetime_ist_str.split(" ")[1]
                #     date_part_vanished, time_part_vanished = vanished_datetime_ist_str.split(" ")

                #     logger.debug(created_datetime)
                #     logger.debug(time_part_created)

                #     logger.debug(vanished_datetime)
                #     logger.debug(date_part_vanished)
                #     logger.debug(time_part_vanished)

                #     _data = {
                #         "images": ["/static_server/app_media/{}/Media/{}".format(
                #                     self.service_name, log["image_url"]
                #                 )],
                #         "camera": log["source_details"]["source_name"],
                #         "alert": log["roi_name"],
                #         "date": date_part_vanished,
                #         "created time": time_part_created,
                #         "vanished time": time_part_vanished,
                #     }
                #     response.append(_data)

##############################

            # for log in DetectionLogs.objects.aggregate(pipeline):
            #     created_datetime = log["created"]
            #     vanished_datetime = log["vanished"]


            #     if created_datetime is not None and vanished_datetime is not None:
            #         _data = {
            #             "images": ["/static_server/app_media/{}/Media/{}".format(
            #                         self.service_name, log["image_url"]
            #                     )],
            #             "camera": log["source_details"]["source_name"],
            #             "alert": log["roi_name"],
            #             "date": vanished_datetime.strftime("%Y-%m-%d"),
            #             "created time": created_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            #             "vanished time": vanished_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            #         }
            #         response.append(_data)


            # logger.debug(response)

            message = {
                "task_name": "widget_settings",
                "func_kwargs": {
                    "session_id": session_id,
                    "widget_id": widget_id,
                    "type": "get",
                    "data": {
                        "live_alerts": {
                            "alert_table": {
                                "data": {
                                    "labels": [],
                                    "datasets": response,
                                    "total": 100,
                                }
                            }
                        },
                        **params,
                    },
                },
            }

            # logger.debug(params)

            logger.debug(message)

            connector.produce_data(
                message=message,
                destination="socket_server",
                event_type="widget_settings",
            )
        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )
        finally:
            self.update_widget_cache(
                user_id, session_id, widget_id, index, params, message
            )
        return


    def send_widget_data(self):
        for user_id in glb.user_sessions:
            for session_id in glb.user_sessions[user_id]:
                for index, widget in enumerate(glb.user_sessions[user_id][session_id]):
                    # logger.debug(widget)
                    params = {}
                    if "user_inputs" in widget:
                        params = widget.pop("user_inputs")
                        # logger.debug(params)
                    widget["params"] = params
                    func_name = "get_{}".format(widget["widget_name"])
                    if func_name:
                        if hasattr(self, func_name) and callable(func := getattr(self, func_name)):
                            try:
                                func(
                                    **{
                                        "user_id": user_id,
                                        "session_id": session_id,
                                        "index": index,
                                        **widget,
                                    }
                                )
                            except Exception as e:
                                logger.error(
                                "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
                            )



# working
# def get_live_alerts(
#         self,
#         user_data=None,
#         params={}, 
#         widget_id="6602aaea005263fb79b1094a", 
#         **kwargs):
#         try:
#             session_id = kwargs["session_id"] if "session_id" in kwargs else None

#             if isinstance(user_data, dict):
#                 user_id = user_data["user_id"]
#                 logger.debug(user_id)
#             else:
#                 user_id = kwargs["user_id"]
#                 logger.debug(user_id)

#             if "index" not in kwargs:
#                 for index, widget in enumerate(glb.user_sessions[user_id][session_id]):
#                     if widget["widget_id"] == widget_id:
#                         kwargs["index"] = index
#                         break

#             index = kwargs.pop("index")

#             pipeline = [
#                 {
#                     "$match": {
#                         "source_details.source_owner": user_id,
#                     },
#                 },
#                 {
#                     "$sort": {
#                         "created": -1,
#                     },
#                 },
#                 {"$limit": 100},
#             ]
            
#             if any(params):
#                 if "filter" in params and params["filter"]:
#                     pipeline[0]["$match"].update(
#                         {
#                             "$expr": {
#                                 "$setIsSubset": [
#                                     ["$source_details.source_name"],
#                                     params["filter"],
#                                 ]
#                             }
#                         }
#                     )
#             elif "user_inputs" in  glb.user_sessions[user_id][session_id][index]:
#                 params = copy.deepcopy(
#                     glb.user_sessions[user_id][session_id][index]["user_inputs"]
#                 )

#             response = []

#             IST = pytz.timezone('Asia/Kolkata')

#             for log in DetectionLogs.objects.aggregate(pipeline):
#                 created_datetime = log["created"]
#                 vanished_datetime = log["vanished"]

#                 # Convert UTC time to IST
#                 created_datetime_ist = created_datetime.astimezone(IST)
#                 vanished_datetime_ist = vanished_datetime.astimezone(IST)

#                 # logger.debug(created_datetime_ist)

#                 created_datetime_ist_str = created_datetime_ist.strftime("%Y-%m-%d %H:%M:%S")
#                 vanished_datetime_ist_str = vanished_datetime_ist.strftime("%Y-%m-%d %H:%M:%S")

#                 time_part_created = created_datetime_ist_str.split(" ")[1]
#                 date_part_vanished, time_part_vanished = vanished_datetime_ist_str.split(" ")

#                 _data = {
#                     "images": ["/static_server/app_media/{}/Media/{}".format(
#                                 self.service_name, log["image_url"]
#                             )],
#                     "camera": log["source_details"]["source_name"],
#                     "alert": log["roi_name"],
#                     "date": date_part_vanished,
#                     "created time": time_part_created,
#                     "vanished time": time_part_vanished,
#                 }
#                 response.append(_data)

#             logger.debug(response)

#             message = {
#                 "task_name": "widget_settings",
#                 "func_kwargs": {
#                     "session_id": session_id,
#                     "widget_id": widget_id,
#                     "type": "get",
#                     "data": {
#                         "live_alerts": {
#                             "alert_table": {
#                                 "data": {
#                                     "labels": [
#                                         "images",
#                                         "camera",
#                                         "alert",
#                                         "date",
#                                         "created time",
#                                         "vanished time",
#                                     ],
#                                     "datasets": response,
#                                     "total": 1,
#                                 }
#                             }
#                         },
#                         **params,
#                     },
#                 },
#             }

#             # logger.debug(params)

#             # logger.debug(message)

#             connector.produce_data(
#                 message=message,
#                 destination="socket_server",
#                 event_type="widget_settings",
#             )
#         except Exception as e:
#             logger.error(
#             "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
#         )
#         finally:
#             self.update_widget_cache(
#                 user_id, session_id, widget_id, index, params, message
#             )
#         return

