import os
import copy
from shapely.geometry import Polygon
import time
import numpy as np
from PIL import Image
import cv2
import io
import threading
import sys

from core.utils import *
import core.globals as glb

from core.rdx_connection_handler import service_details, logger


class LogicHandler:
    def __init__(self) -> None:
        self.connector = connector
        self.object_tracker = {}

        self.alert_metadata = {
            "service_name": service_details["SERVICE_NAME"],
            "service_tags": service_details["SERVICE_SETTINGS"]["SERVICE_TAGS"].split(
                ","
            ),
            "sources": [],
            "target_service": [],
            "output_data": [],
            "date_time": None,
        }

        self.image_storage_path = os.path.join(os.getcwd(), "custom_data")
        if "SERVICE_MOUNTS" in service_details:
            self.image_storage_path = service_details["SERVICE_MOUNTS"]["output_media"]
        # threading.Thread(target=self.post_action, daemon=True).start()

        # self.scheduler = BackgroundScheduler(timezone=utc)
        # self.scheduler.add_job(partial(self.clear_cache, self.object_tracker), 'interval', seconds=20)
        # self.scheduler.start()

    def post_iot_action(self):
        pass

    # def post_action(self):
    #     pass
    #     while not glb.message_queue.empty() or glb.message_queue.qsize != 0:
    #         alert_data = glb.message_queue.get()
    #         data = {
    #             "task_name": "action",
    #             "func_kwargs": {
    #                 "data": {
    #                     "app_details": {
    #                         "app_name": alert_data["data"]["service_name"],
    #                         "tab_name": "general_settings",
    #                         "section_name": "action_on_patient_detection",
    #                     },
    #                     "user_data": glb.sources_list[alert_data["index"]][
    #                         "user"
    #                     ].payload(),
    #                     "type": "alert",
    #                     "alert_text": alert_data["data"]["output_data"][0][
    #                         "alert_text"
    #                     ],
    #                     "source_name": glb.sources_list[alert_data["index"]]["source"][
    #                         "source_name"
    #                     ],
    #                     "date_time": alert_data["data"]["date_time"],
    #                     "metadata": alert_data["data"]["output_data"][0]["metadata"],
    #                 }
    #             },
    #         }

    #         try:
    #             general_settings = GeneralSettings.objects.get(
    #                 output_name="action_on_patient_detection",
    #                 user_details=glb.sources_list[alert_data["index"]]["user"],
    #             )

    #             for action in general_settings.settings["actions"]:
    #                 connector.produce_data(
    #                     message=data,
    #                     key=alert_data["key"],
    #                     headers=alert_data["headers"],
    #                     transaction_id=alert_data["transaction_id"],
    #                     event_type="action",
    #                     destination=action,
    #                 )
    #         except:
    #             pass
    #     time.sleep(0.1)
    #     self.post_action()

    def post_action(self, index, alert_data, key, headers, transaction_id):
        data = {
            "task_name": "action",
            "func_kwargs": {
                "data": {
                    "app_details": {
                        "app_name": alert_data["service_name"],
                        "tab_name": "general_settings",
                        "section_name": "action_on_person_trespassed",
                    },
                    "user_data": glb.sources_list[index]["user"].payload(),
                    "type": "alert",
                    "alert_text": alert_data["output_data"][0]["alert_text"],
                    "source_name": glb.sources_list[index]["source"]["source_name"],
                    "date_time": alert_data["date_time"],
                }
            },
        }
        
        general_settings = GeneralSettings.objects.get(
            output_name="action_on_person_trespassed",
            user_details=glb.sources_list[index]["user"],
        )

        for action in general_settings.settings["actions"]:
            connector.produce_data(
                message=data,
                key=key,
                headers=headers,
                transaction_id=transaction_id,
                event_type="action",
                destination=action,
            )

        # storage_path=self.image_storage_path,
        # alert_schema=copy.deepcopy(self.alert_metadata),
        # index=_id,
        # detected_object=copy.deepcopy(detected_object),
        # key=key,
        # headers=source_details,
        # transaction_id=transaction_id,
        # **data, 

        # alert_schema=copy.deepcopy(self.alert_metadata),
        # storage_path=self.image_storage_path,
        # compliance_check_info = copy.deepcopy(compliance_check_info),
        # index=_id,
        # detected_object=copy.deepcopy(detected_object),
        # key=key,
        # headers=source_details,
        # transaction_id=transaction_id,
        # **data,     

    def post_process(
        self,
        alert_schema,
        compliance_check_info,
        index,
        detected_object,
        key,
        headers,
        transaction_id,
        **kwargs,
    ):
        logger.debug(headers)
        logger.debug(compliance_check_info)

        medias = []

        metadata = connector.consume_from_source(
            topic=headers["topic"], 
            partition=headers["partition"], 
            offset=headers["offset"]
        )
        if metadata:
            nparr = np.frombuffer(metadata, np.uint8)
            raw_image = Image.open(io.BytesIO(nparr))
            image_rgb = np.array(raw_image)
            image_np_array = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            image_name = "{}.jpg".format(
                datetime.datetime.utcnow().strftime("%d-%m-%Y_%H-%M-%S-%f")
            )
            sub_folder = os.path.join(
                datetime.datetime.utcnow().strftime("%Y-%m-%d"), "Image"
            )
            
            if not os.path.exists(os.path.join(self.image_storage_path, sub_folder)):
                os.makedirs(os.path.join(self.image_storage_path, sub_folder))

            image_path = os.path.join(self.image_storage_path, sub_folder, image_name)
            cv2.imwrite(image_path, image_np_array)
            # logger.info(image_path)

# compliance_check_info[object_id] = {
#     "object_metadata": object_polygons[object_id]["detected_object"],
#     "source_details": SourceDetails(
#         **glb.sources_list[int(object_polygons[object_id]["index"])][
#             "source"
#         ].logs_payload()
#     ),
#     "user_data": glb.sources_list[int(object_polygons[object_id]["index"])][
#         "user"
#     ],
#     "detected_objects": detected_object["name"],
#     "roi_details": copy.deepcopy(
#         glb.sources_list[int(object_polygons[object_id]["index"])]["roi"]
#     ),
# }

            for _, person_data in compliance_check_info.items():
                # detected_objects_dict = {
                #     "helmet": {"wearing": False, "not wearing": True},
                #     "safety_vest": {"wearing": False, "not wearing": True},
                #     "harness": {"wearing": False, "not wearing": True},
                # }
                # for _object in person_data.pop("detected_objects"):
                #     detected_objects_dict[_object]["wearing"] = True
                #     detected_objects_dict[_object]["not wearing"] = False
                DetectionLogs(
                    image_url=os.path.join(sub_folder, image_name),
                    image_width=headers["source_frame_width"],
                    image_height=headers["source_frame_height"],
                    **person_data,
                ).save()

                # logger.debug(compliance_check_info)

            __metadata = {
                "confidence": detected_object.pop("confidence"),
                "name": detected_object.pop("name"),
                "object_id": detected_object.pop("object_id"),
                "bounding_box": detected_object,
            }

            # logger.debug(__metadata)

            # logger.debug(headers["source_frame_width"])
            # logger.debug(glb.sources_list[index]["roi"])
            medias = [
                {
                    "media_link": os.path.join(sub_folder, image_name),
                    "media_width": headers["source_frame_width"],
                    "media_height": headers["source_frame_height"],
                    "media_type": "image",
                    "roi_details": [copy.deepcopy(glb.sources_list[index]["roi"])],
                    "detections": [__metadata],
                }
            ]


        alert_schema["group_name"] = headers["source_name"]
        alert_schema["sources"] = [glb.sources_list[index]["source"].payload()]
        alert_schema["date_time"] = "{}Z".format(datetime.datetime.utcnow()).replace(
            " ", "T"
        )
        alert_schema["output_data"].append(
            {
                "transaction_id": transaction_id,
                "output": "patient detection",
                "priority": "medium",
                "alert_text": "patient detection in region {}".format(
                    glb.sources_list[index]["roi"]["roi_name"]
                ),
                "metadata": medias,
            }
        )

        connector.produce_data(
            message={
                "task_name": "alert",
                "metadata": alert_schema,
                **kwargs,
            },
            key=key,
            headers=headers,
            transaction_id=transaction_id,
            event_type="alert",
            destination="alert_management",
        )
        
        self.post_action(index, alert_schema, key, headers, transaction_id)


    def clear_cache(self, sample_generator):
        utc_now = datetime.datetime.utcnow()
        five_minutes_ago = datetime.timedelta(seconds=10)
        
        objects_to_remove = []
        for object_id, object_data in sample_generator.items():
            last_detected_time = object_data.get("last_detected")
            created_time = object_data.get("created")
            if last_detected_time is not None and (utc_now - last_detected_time) > five_minutes_ago:
                objects_to_remove.append(object_id)
            elif last_detected_time is None and (utc_now - created_time) > five_minutes_ago:
                objects_to_remove.append(object_id)
                # logger.debug(object_id)
        
        # logger.debug(objects_to_remove)
        # Remove objects from sample_generator
        for object_id in objects_to_remove:
            # logger.debug(sample_generator)
            del sample_generator[object_id]
            # logger.debug(self.object_tracker)
        # objects_to_remove.clear()


    # def process_data(self, data, **kwargs):
    #     try:
    #         utc_now = datetime.datetime.utcnow()
    #         transaction_id = kwargs.pop("transaction_id")
    #         key = kwargs.pop("key")
    #         source_details = kwargs.pop("headers")

    #         try:
    #             _ = glb.loaded_camera_ids[source_details["source_id"]]
    #         except KeyError:
    #             load_configuration_settings(**source_details)

    #         person_polygons = {}
    #         other_object_polygons = {}

    #         loaded_camera = glb.loaded_camera_ids[source_details["source_id"]]["indexes"] 

    #         for detected_object in copy.deepcopy(data["detections"]):
    #             x1, y1 = detected_object["x1"], detected_object["y1"]
    #             x2, y2 = detected_object["x2"], detected_object["y2"]
    #             x3, y3 = detected_object["x3"], detected_object["y3"]
    #             x4, y4 = detected_object["x4"], detected_object["y4"]

    #             detected_polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

    #             if detected_object["name"] == glb.object_class_name and detected_object["confidence"] >= 0.8:
    #                 for _id in loaded_camera:
    #                     if glb.polygons[_id].contains(detected_polygon):
    #                         object_id = "{}_{}_{}".format(
    #                             source_details["source_id"],
    #                             glb.sources_list[_id]["roi"]["roi_name"],
    #                             detected_object["object_id"],
    #                         )

    #                         person_polygons[object_id] = {
    #                                 "index": _id,
    #                                 "object_metadata": copy.deepcopy(detected_object),
    #                                 "top": detected_object["y1"],
    #                                 "height": detected_object["y2"] - detected_object["y1"],
    #                                 "polygon": detected_polygon,
    #                             }
                           
    #                         if object_id not in self.object_tracker:
    #                             self.object_tracker[object_id] = {
    #                                 "last_detected": None,
    #                                 "created": utc_now,
    #                                 "alert": False,
    #                                 "detected_object": copy.deepcopy(detected_object),
    #                                 "polygon": detected_polygon,  # Store the Polygon object
    #                             }
                                
    #                         if self.object_tracker[object_id]["alert"]:
    #                             if self.object_tracker[object_id]['last_detected']:
                                    
    #                                 glb.sample_generator[object_id] = self.object_tracker[object_id]
    #                                 self.object_tracker[object_id]["last_detected"] = utc_now

    #                         if not self.object_tracker[object_id]["alert"]:
    #                             time_diff = (
    #                                 utc_now - self.object_tracker[object_id]["created"]
    #                             ).seconds
    #                             if time_diff >= 0:
    #                                 self.object_tracker[object_id]["alert"] = True
    #                                 self.object_tracker[object_id]["last_detected"] = utc_now
    #                                 self.post_process(
    #                                     storage_path=self.image_storage_path,
    #                                     alert_schema=copy.deepcopy(self.alert_metadata),
    #                                     index=_id,
    #                                     detected_object=copy.deepcopy(detected_object),
    #                                     key=key,
    #                                     headers=source_details,
    #                                     transaction_id=transaction_id,
    #                                     **data,
    #                                 )
    #     except Exception as e:
    #         logger.error("Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e))


    def process_data(self, data, **kwargs):
        try:
            # logger.debug(glb.user_sessions)
            # start_time = time.time()
            # logger.info(time.time() - start_time)
            # logger.debug(data)

            utc_now = datetime.datetime.utcnow()

            transaction_id = kwargs.pop("transaction_id")
            key = kwargs.pop("key")
            source_details = kwargs.pop("headers")

            try:
                _ = glb.loaded_camera_ids[source_details["source_id"]]
            except KeyError:
                load_configuration_settings(**source_details)

            loaded_camera = glb.loaded_camera_ids[source_details["source_id"]]["indexes"] 

            compliance_check_info = {}
            object_polygons = {}
            

            for detected_object in copy.deepcopy(data["detections"]):
                if detected_object["name"] == glb.object_class_name and detected_object["confidence"] >= 0.8:
                    x1, y1 = detected_object["x1"], detected_object["y1"]
                    x2, y2 = detected_object["x2"], detected_object["y2"]
                    x3, y3 = detected_object["x3"], detected_object["y3"]
                    x4, y4 = detected_object["x4"], detected_object["y4"]

                    detected_polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

                    x_coordinate = (detected_object["x1"] + detected_object["x2"]) // 2
                    y_coordinate = (detected_object["y1"] + detected_object["y4"]) // 2

                    for _id in loaded_camera:
                        if glb.polygons[_id].contains(detected_polygon):
                            object_id = "{}_{}_{}".format(
                                source_details["source_id"],
                                glb.sources_list[_id]["roi"]["roi_name"],
                                detected_object["object_id"],
                            )
                            
                            object_polygons[object_id] = {
                                "index": _id,
                                "name": detected_object["name"],
                                "last_detected": None,
                                "created": utc_now,
                                "alert": False,
                                "detected_object": copy.deepcopy(detected_object),
                                "polygon": detected_polygon,
                            }

                            if object_id not in self.object_tracker:
                                self.object_tracker[object_id] = {
                                    "last_detected": None,
                                    "created": utc_now,
                                    "alert": False,
                                    "detected_object": copy.deepcopy(detected_object),
                                    "polygon": detected_polygon,  # Store the Polygon object
                                }

                            if self.object_tracker[object_id]["alert"]:
                                if self.object_tracker[object_id]['last_detected']:
                                    
                                    glb.sample_generator[object_id] = self.object_tracker[object_id]
                                    self.object_tracker[object_id]["last_detected"] = utc_now

                            # "source_details": SourceInfo(
                            #     **glb.sources_list[int(object_polygons[object_id]["index"])][
                            #         "source"
                            #     ].logs_payload()
                            # ),

                            # "source_details": SourceInfo(
                            #     source_id=glb.sources_list[int(object_polygons[object_id]["index"])]["source"]["source_id"],
                            #     source_name=glb.sources_list[int(object_polygons[object_id]["index"])]["source"]["source_name"],
                            #     source_owner={"owner_key": "owner_value"}  # Provide a dictionary for source_owner
                            # ),

                            if not self.object_tracker[object_id]["alert"]:
                                time_diff = (utc_now - self.object_tracker[object_id]["created"]).seconds
                                if time_diff >= 0:
                                    compliance_check_info[object_id] = {
                                        "object_metadata": object_polygons[object_id]["detected_object"],
                                        
                                        "source_details": SourceDetails(
                                            **glb.sources_list[int(object_polygons[object_id]["index"])][
                                                "source"
                                            ].logs_payload()
                                        ),

                                        "user_data": glb.sources_list[int(object_polygons[object_id]["index"])][
                                            "user"
                                        ],
                                        "roi_details": copy.deepcopy(
                                            glb.sources_list[int(object_polygons[object_id]["index"])]["roi"]
                                        ),
                                        "area": "patient detection in region {}".format(
                                            glb.sources_list[_id]["roi"]["roi_name"]
                                        ),
                                    }

                                    logger.debug(compliance_check_info[object_id]["source_details"]["source_owner"])

                                    self.object_tracker[object_id]["alert"] = True
                                    self.object_tracker[object_id]["last_detected"] = utc_now
                                    self.post_process(
                                        storage_path=self.image_storage_path,
                                        compliance_check_info = copy.deepcopy(compliance_check_info),
                                        alert_schema=copy.deepcopy(self.alert_metadata),
                                        index=_id,
                                        detected_object=copy.deepcopy(detected_object),
                                        key=key,
                                        headers=source_details,
                                        transaction_id=transaction_id,
                                        **data,
                                    )


            # for detected_object in copy.deepcopy(data["detections"]):
            #     x1, y1 = detected_object["x1"], detected_object["y1"]
            #     x2, y2 = detected_object["x2"], detected_object["y2"]
            #     x3, y3 = detected_object["x3"], detected_object["y3"]
            #     x4, y4 = detected_object["x4"], detected_object["y4"]

            #     detected_polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

            #     if detected_object["name"] == glb.object_class_name and detected_object["confidence"] >= 0.8:
            #         # x_coordinate = (detected_object["x1"] + detected_object["x2"]) // 2
            #         # y_coordinate = (detected_object["y1"] + detected_object["y4"]) // 2

            #         # for _id in glb.loaded_camera_ids[source_details["source_id"]][
            #         #     "indexes"
            #         # ]:
            #         #     if Point(x_coordinate, y_coordinate).within(glb.polygons[_id]):
            #         #         if detected_object["name"] == "person":

            #         #             person_id = "{}_{}_{}".format(
            #         #                 source_details["source_id"],
            #         #                 glb.sources_list[_id]["roi"]["roi_name"],
            #         #                 detected_object["object_id"],
            #         #             )

            #         for _id in loaded_camera:
            #             if glb.polygons[_id].contains(detected_polygon):
            #                 object_id = "{}_{}_{}".format(
            #                     source_details["source_id"],
            #                     glb.sources_list[_id]["roi"]["roi_name"],
            #                     detected_object["object_id"],
            #                 )

            #                 if object_id not in self.object_tracker:
            #                     self.object_tracker[object_id] = {
            #                         "last_detected": None,
            #                         "created": utc_now,
            #                         "alert": False,
            #                         "detected_object": copy.deepcopy(detected_object),
            #                         "polygon": detected_polygon,  # Store the Polygon object
            #                     }
                                
            #                 if self.object_tracker[object_id]["alert"]:
            #                     if self.object_tracker[object_id]['last_detected']:
                                    
            #                         glb.sample_generator[object_id] = self.object_tracker[object_id]
            #                         self.object_tracker[object_id]["last_detected"] = utc_now

            #                 if not self.object_tracker[object_id]["alert"]:
            #                     time_diff = (
            #                         utc_now - self.object_tracker[object_id]["created"]
            #                     ).seconds
            #                     if time_diff >= 0:
            #                         self.object_tracker[object_id]["alert"] = True
            #                         self.object_tracker[object_id]["last_detected"] = utc_now
            #                         # logger.debug(glb.polygons[_id])
            #                         # logger.debug(detected_polygon)
            #                         # logger.debug(detected_object)
            #                         # logger.debug(glb.sample_generator)
            #                         self.post_process(
            #                             storage_path=self.image_storage_path,
            #                             alert_schema=copy.deepcopy(self.alert_metadata),
            #                             index=_id,
            #                             detected_object=copy.deepcopy(detected_object),
            #                             key=key,
            #                             headers=source_details,
            #                             transaction_id=transaction_id,
            #                             **data,
            #                         )
        

        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )


logicHandler = LogicHandler()


# class LogicHandler:
#     def __init__(self) -> None:
#         self.object_tracker = {}

#         self.alert_metadata = {
#             "service_name": service_details["SERVICE_NAME"],
#             "service_tags": service_details["SERVICE_SETTINGS"]["SERVICE_TAGS"].split(
#                 ","
#             ),
#             "sources": [],
#             "target_service": [],
#             "output_data": [],
#             "date_time": None,
#         }

#         self.image_storage_path = os.path.join(os.getcwd(), "custom_data")
#         if "SERVICE_MOUNTS" in service_details:
#             self.image_storage_path = service_details["SERVICE_MOUNTS"]["output_media"]
#         threading.Thread(target=self.post_action, daemon=True).start()

#     def post_action(self):
#         pass
#         # while not glb.message_queue.empty() or glb.message_queue.qsize != 0:
#         #     alert_data = glb.message_queue.get()
#         #     data = {
#         #         "task_name": "action",
#         #         "func_kwargs": {
#         #             "data": {
#         #                 "app_details": {
#         #                     "app_name": alert_data["data"]["service_name"],
#         #                     "tab_name": "general_settings",
#         #                     "section_name": "action_on_patient_detection",
#         #                 },
#         #                 "user_data": glb.sources_list[alert_data["index"]][
#         #                     "user"
#         #                 ].payload(),
#         #                 "type": "alert",
#         #                 "alert_text": alert_data["data"]["output_data"][0][
#         #                     "alert_text"
#         #                 ],
#         #                 "source_name": glb.sources_list[alert_data["index"]]["source"][
#         #                     "source_name"
#         #                 ],
#         #                 "date_time": alert_data["data"]["date_time"],
#         #                 "metadata": alert_data["data"]["output_data"][0]["metadata"],
#         #             }
#         #         },
#         #     }

#         #     try:
#         #         general_settings = GeneralSettings.objects.get(
#         #             output_name="action_on_patient_detection",
#         #             user_details=glb.sources_list[alert_data["index"]]["user"],
#         #         )

#         #         for action in general_settings.settings["actions"]:
#         #             connector.produce_data(
#         #                 message=data,
#         #                 key=alert_data["key"],
#         #                 headers=alert_data["headers"],
#         #                 transaction_id=alert_data["transaction_id"],
#         #                 event_type="action",
#         #                 destination=action,
#         #             )
#         #     except:
#         #         pass
#         # time.sleep(0.1)
#         # self.post_action()

#     def post_iot_action(self):
#         pass

#     def post_process(
#         self,
#         classwise_segregation: dict,
#         compliance_check_info: dict,
#         key: str,
#         headers: dict,
#         transaction_id: str,
#         **kwargs,
#     ):
#         pass
#         # metadata = connector.consume_from_source(
#         #     topic=headers["topic"],
#         #     partition=headers["partition"],
#         #     offset=headers["offset"],
#         # )
#         # if metadata:
#         #     nparr = np.frombuffer(metadata, np.uint8)
#         #     raw_image = Image.open(io.BytesIO(nparr))
#         #     image_rgb = np.array(raw_image)
#         #     image_np_array = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
#         #     image_name = "{}.jpg".format(
#         #         datetime.datetime.utcnow().strftime("%d-%m-%Y_%H-%M-%S-%f")
#         #     )
#         #     sub_folder = os.path.join(
#         #         datetime.datetime.utcnow().strftime("%Y-%m-%d"), "Image"
#         #     )
#         #     if not os.path.exists(os.path.join(self.image_storage_path, sub_folder)):
#         #         os.makedirs(os.path.join(self.image_storage_path, sub_folder))

#         #     image_path = os.path.join(self.image_storage_path, sub_folder, image_name)
#         #     cv2.imwrite(image_path, image_np_array)
#         #     logger.info(image_path)

#         #     for _, person_data in compliance_check_info.items():
#         #         detected_objects_dict = {
#         #             "helmet": {"wearing": False, "not wearing": True},
#         #             "safety_vest": {"wearing": False, "not wearing": True},
#         #             "harness": {"wearing": False, "not wearing": True},
#         #         }
#         #         for _object in person_data.pop("detected_objects"):
#         #             detected_objects_dict[_object]["wearing"] = True
#         #             detected_objects_dict[_object]["not wearing"] = False
#         #         DetectionLogs(
#         #             detected_objects=detected_objects_dict,
#         #             image_url=os.path.join(sub_folder, image_name),
#         #             image_width=headers["source_frame_width"],
#         #             image_height=headers["source_frame_height"],
#         #             **person_data,
#         #         ).save()

#         #     for _class, _roi_wise_detection in classwise_segregation.items():
#         #         for _index, detected_objects in _roi_wise_detection.items():
#         #             if _class in glb.sources_list[int(_index)]["allowed_objects"]:
#         #                 alert_schema = copy.deepcopy(self.alert_metadata)
#         #                 _detected_objects = copy.deepcopy(detected_objects)
#         #                 classwise_detected_objects = []
#         #                 for _detected_object_index, _detected_object in enumerate(
#         #                     _detected_objects
#         #                 ):
#         #                     _detected_object.pop("index")
#         #                     transformed_object = {
#         #                         "confidence": _detected_object["object_metadata"].pop(
#         #                             "confidence"
#         #                         ),
#         #                         "name": _detected_object["object_metadata"].pop("name"),
#         #                         "object_id": _detected_object["object_metadata"].pop(
#         #                             "object_id"
#         #                         ),
#         #                         "bounding_box": _detected_object["object_metadata"],
#         #                     }
#         #                     classwise_detected_objects.append(transformed_object)

#         #                     if (
#         #                         "head" in _detected_object
#         #                         and _class == "helmet"
#         #                         and glb.include_head
#         #                     ):
#         #                         _detected_object = copy.deepcopy(_detected_object).pop(
#         #                             "head"
#         #                         )
#         #                         _detected_object.pop("index")
#         #                         head_object = {
#         #                             "confidence": _detected_object[
#         #                                 "object_metadata"
#         #                             ].pop("confidence"),
#         #                             "name": _detected_object["object_metadata"].pop(
#         #                                 "name"
#         #                             ),
#         #                             "object_id": _detected_object[
#         #                                 "object_metadata"
#         #                             ].pop("object_id"),
#         #                             "bounding_box": _detected_object["object_metadata"],
#         #                         }
#         #                         classwise_detected_objects.append(head_object)

#         #                 medias = [
#         #                     {
#         #                         "media_link": os.path.join(sub_folder, image_name),
#         #                         "media_width": headers["source_frame_width"],
#         #                         "media_height": headers["source_frame_height"],
#         #                         "media_type": "image",
#         #                         "roi_details": [
#         #                             copy.deepcopy(glb.sources_list[int(_index)]["roi"])
#         #                         ],
#         #                         "detections": copy.deepcopy(classwise_detected_objects),
#         #                     }
#         #                 ]

#         #                 alert_schema["group_name"] = headers["source_name"]
#         #                 alert_schema["sources"] = [
#         #                     glb.sources_list[int(_index)]["source"].payload(
#         #                         user_details=glb.sources_list[int(_index)][
#         #                             "user"
#         #                         ].payload()
#         #                     )
#         #                 ]
#         #                 alert_schema["date_time"] = "{}Z".format(
#         #                     datetime.datetime.utcnow()
#         #                 ).replace(" ", "T")

#         #                 alert_schema["output_data"].append(
#         #                     {
#         #                         "transaction_id": transaction_id,
#         #                         "output": "Safety compliance",
#         #                         "priority": "high",
#         #                         "alert_text": "person is not wearing {} in region {}".format(
#         #                             _class.replace("_", " "),
#         #                             glb.sources_list[int(_index)]["roi"]["roi_name"],
#         #                         ),
#         #                         "metadata": medias,
#         #                     }
#         #                 )
#         #                 connector.produce_data(
#         #                     message={
#         #                         "task_name": "alert",
#         #                         "metadata": alert_schema,
#         #                         **kwargs,
#         #                     },
#         #                     key=key,
#         #                     headers=headers,
#         #                     transaction_id=transaction_id,
#         #                     event_type="alert",
#         #                     destination="alert_management",
#         #                 )
#         #                 logger.info(
#         #                     f"{_class.replace('_', '')} Missing Alert Generated"
#         #                 )
#         #                 if glb.sources_list[int(_index)]["voice_command_enable"]:
#         #                     glb.iot_command_queue.put({
#         #                         "url": glb.sources_list[int(_index)][
#         #                             "voice_command_server_url"
#         #                         ],
#         #                         "message": _class.replace("_", " ")
#         #                     })
#         #                 glb.message_queue.put(
#         #                     {
#         #                         "data": copy.deepcopy(alert_schema),
#         #                         "index": int(_index),
#         #                         "key": key,
#         #                         "headers": headers,
#         #                         "transaction_id": transaction_id,
#         #                     }
#         #                 )


#     def process_data(self, data, **kwargs):
#         pass
#         try:
#             logger.debug(data)
#         except Exception as e:
#             logger.error(
#             "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
#         )
#         # start_time = time.time()
#         # transaction_id = kwargs.pop("transaction_id")
#         # key = kwargs.pop("key")
#         # source_details = kwargs.pop("headers")

#         # try:
#         #     _ = glb.loaded_camera_ids[source_details["source_id"]]
#         # except KeyError:
#         #     load_configuration_settings(**source_details)

#         # person_polygons = {}
#         # other_object_polygons = {}

#         # for detected_object in copy.deepcopy(data["detections"]):
#         #     if (
#         #         detected_object["confidence"]
#         #         >= glb.confidence_threshold[detected_object["name"]]
#         #     ):
#         #         x_coordinate = (detected_object["x1"] + detected_object["x2"]) // 2
#         #         y_coordinate = (detected_object["y1"] + detected_object["y4"]) // 2

#         #         for _id in glb.loaded_camera_ids[source_details["source_id"]][
#         #             "indexes"
#         #         ]:
#         #             if Point(x_coordinate, y_coordinate).within(glb.polygons[_id]):
#         #                 if detected_object["name"] == "person":

#         #                     person_id = "{}_{}_{}".format(
#         #                         source_details["source_id"],
#         #                         glb.sources_list[_id]["roi"]["roi_name"],
#         #                         detected_object["object_id"],
#         #                     )

#         #                     person_polygons[person_id] = {
#         #                         "index": _id,
#         #                         "object_metadata": copy.deepcopy(detected_object),
#         #                         "top": detected_object["y1"],
#         #                         "height": detected_object["y2"] - detected_object["y1"],
#         #                         "polygon": Polygon(
#         #                             [
#         #                                 (detected_object["x1"], detected_object["y1"]),
#         #                                 (detected_object["x2"], detected_object["y2"]),
#         #                                 (detected_object["x3"], detected_object["y3"]),
#         #                                 (detected_object["x4"], detected_object["y4"]),
#         #                             ]
#         #                         ),
#         #                     }
#         #                 else:
#         #                     other_object_polygons[detected_object["object_id"]] = {
#         #                         "index": _id,
#         #                         "name": detected_object["name"],
#         #                         "object_metadata": copy.deepcopy(detected_object),
#         #                         "top": detected_object["y1"] + glb.padding,
#         #                         "height": detected_object["y2"] - detected_object["y1"],
#         #                         "polygon": Polygon(
#         #                             [
#         #                                 (
#         #                                     detected_object["x1"],
#         #                                     detected_object["y1"] + glb.padding,
#         #                                 ),
#         #                                 (
#         #                                     detected_object["x2"],
#         #                                     detected_object["y2"] + glb.padding,
#         #                                 ),
#         #                                 (detected_object["x3"], detected_object["y3"]),
#         #                                 (detected_object["x4"], detected_object["y4"]),
#         #                             ]
#         #                         ),
#         #                     }

#         # detections = {}
#         # used_object_ids = []
#         # compliance_check_info = {}

#         # if (
#         #     datetime.datetime.utcnow() - glb.last_alert_generated
#         # ).seconds < glb.max_time_threshold:
#         #     return

#         # classwise_segregation = {"helmet": {}, "safety_vest": {}, "harness": {}}
#         # for person_id, person_data in copy.deepcopy(person_polygons).items():
#         #     if person_id not in detections:
#         #         detections[person_id] = []
#         #     for object_id, object_data in other_object_polygons.items():
#         #         if object_id not in used_object_ids:
#         #             if object_data["polygon"].within(person_data["polygon"]):

#         #                 if object_data["name"] == "head":
#         #                     person_polygons[person_id]["head"] = copy.deepcopy(
#         #                         object_data
#         #                     )
#         #                 elif object_data["name"] in [
#         #                     "safety_vest",
#         #                     "harness",
#         #                     "helmet",
#         #                 ]:
#         #                     used_object_ids.append(object_id)
#         #                     if object_data["name"] not in detections[person_id]:
#         #                         detections[person_id].append(object_data["name"])

#         #     compliance_check_info[person_id] = {
#         #         "object_metadata": person_polygons[person_id]["object_metadata"],
#         #         "source_details": SourceDetails(
#         #             **glb.sources_list[int(person_polygons[person_id]["index"])][
#         #                 "source"
#         #             ].logs_payload()
#         #         ),
#         #         "user_data": glb.sources_list[int(person_polygons[person_id]["index"])][
#         #             "user"
#         #         ],
#         #         "detected_objects": detections[person_id],
#         #         "roi_details": copy.deepcopy(
#         #             glb.sources_list[int(person_polygons[person_id]["index"])]["roi"]
#         #         ),
#         #     }

#         #     if person_id in detections and len(detections[person_id]) == 3:
#         #         del person_polygons[person_id]
#         #     else:
#         #         for _class in classwise_segregation:
#         #             if _class not in detections[person_id]:
#         #                 if (
#         #                     str(person_polygons[person_id]["index"])
#         #                     not in classwise_segregation[_class]
#         #                 ):
#         #                     classwise_segregation[_class][
#         #                         "{}".format(person_polygons[person_id]["index"])
#         #                     ] = []
#         #                 classwise_segregation[_class][
#         #                     "{}".format(person_polygons[person_id]["index"])
#         #                 ].append(person_polygons[person_id])

#         # if len(person_polygons.keys()):
#         #     glb.last_alert_generated = datetime.datetime.utcnow()
#         #     self.post_process(
#         #         classwise_segregation=copy.deepcopy(classwise_segregation),
#         #         compliance_check_info=copy.deepcopy(compliance_check_info),
#         #         key=key,
#         #         headers=source_details,
#         #         transaction_id=transaction_id,
#         #         **data,
#         #     )
#         # logger.info(time.time() - start_time)
