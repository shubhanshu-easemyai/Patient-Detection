import os
import copy
from shapely.geometry import Polygon, Point
import time
import numpy as np
from PIL import Image
import cv2
import io
import threading
import sys
from mongoengine.errors import DoesNotExist

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

    def post_process(
        self,
        object_id,
        alert_schema,
        compliance_check_info,
        index,
        detected_object,
        key,
        headers,
        transaction_id,
        alert_text,
        **kwargs,
    ):
        logger.debug(os.path.getsize('/home/easemyai/code/collected_data/'))
        logger.debug(alert_text)
        # logger.debug(headers)
        # logger.debug(compliance_check_info)

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

            # Process compliance_check_info and save to DetectionLogs
            self.process_compliance_check_info(
                object_id, compliance_check_info, sub_folder, image_name, headers
            )

            logger.debug(os.path.join(sub_folder, image_name))

            # Construct medias list
            medias = [
                {
                    "media_link": os.path.join(sub_folder, image_name),
                    "media_width": headers["source_frame_width"],
                    "media_height": headers["source_frame_height"],
                    "media_type": "image",
                    "roi_details": [copy.deepcopy(glb.sources_list[index]["roi"])],
                    "detections": [
                        {
                            "confidence": detected_object.pop("confidence"),
                            "name": detected_object.pop("name"),
                            "object_id": detected_object.pop("object_id"),
                            "bounding_box": detected_object,
                        }
                    ],
                }
            ]

            logger.debug(medias)

        # Construct alert text based on the input parameter
        alert_text_formatted = alert_text.format(
            glb.sources_list[index]["roi"]["roi_name"]
        )

        # Construct alert schema
        alert_schema["group_name"] = headers["source_name"]
        alert_schema["sources"] = [glb.sources_list[index]["source"].payload()]
        alert_schema["date_time"] = "{}Z".format(datetime.datetime.utcnow()).replace(
            " ", "T"
        )
        # alert_schema["output_data"].append(
        #     {
        #         "transaction_id": transaction_id,
        #         "output": "patient detection",
        #         "priority": "medium",
        #         "alert_text": "patient detection in region {}".format(
        #             glb.sources_list[index]["roi"]["roi_name"]
        #         ),
        #         "metadata": medias,
        #     }
        # )
        alert_schema["output_data"].append(
            {
                "transaction_id": transaction_id,
                "output": "patient detection",
                "priority": "medium",
                "alert_text": alert_text_formatted,
                "metadata": medias,
            }
        )
    

        # Produce data
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


    def process_compliance_check_info(
            self, object_id, compliance_check_info, sub_folder, image_name, headers
    ):
        try:
            if DetectionLogs.objects(object_id=object_id).update_one(set__vanished=datetime.datetime.utcnow):
                logger.debug("Updated old") 
            else:
                for _, person_data in compliance_check_info.items():
                    logger.debug(person_data)
                    image_url = os.path.join(sub_folder, image_name)
                    # query = {"object_id": object_id}

                    DetectionLogs(
                        image_url=image_url,
                        image_width=headers["source_frame_width"],
                        image_height=headers["source_frame_height"],
                        **person_data,
                    ).save()
                    logger.debug("New entry created")
        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )

        


    # def process_compliance_check_info(
    #         self, object_id, compliance_check_info, sub_folder, image_name, headers
    # ):
    #     for _, person_data in compliance_check_info.items():
    #         logger.debug(person_data)
    #         DetectionLogs(
    #             image_url=os.path.join(sub_folder, image_name),
    #             image_width=headers["source_frame_width"],
    #             image_height=headers["source_frame_height"],
    #             **person_data,
    #         ).save()


    def clear_cache(self, sample_generator):
        utc_now = datetime.datetime.now()
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


    def process_data(self, data, **kwargs):
        try:
            # logger.debug(glb.user_sessions)
            # start_time = time.time()
            # logger.info(time.time() - start_time)
            # logger.debug(data)

            utc_now = datetime.datetime.utcnow()
            # time_utc_now = datetime.datetime.utcnow()
            # logger.debug(utc_now)
            # logger.debug(time_utc_now)

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

            # for detected_object in copy.deepcopy(data["detections"]):
            #     if detected_object["name"] == glb.object_class_name and detected_object["confidence"] >= 0.8:
            #         x1, y1 = detected_object["x1"], detected_object["y1"]
            #         x2, y2 = detected_object["x2"], detected_object["y2"]
            #         x3, y3 = detected_object["x3"], detected_object["y3"]
            #         x4, y4 = detected_object["x4"], detected_object["y4"]

            #         detected_polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])
            #         x_coordinate = (detected_object["x1"] + detected_object["x2"]) // 2
            #         y_coordinate = (detected_object["y1"] + detected_object["y4"]) // 2
            #         centroid = Point(x_coordinate, y_coordinate)

            #         for _id in loaded_camera:
            #             object_id = "{}_{}_{}".format(
            #                 source_details["source_id"],
            #                 glb.sources_list[_id]["roi"]["roi_name"],
            #                 detected_object["object_id"],
            #             )
            #             object_polygons[object_id] = {
            #                 "index": _id,
            #                 "name": detected_object["name"],
            #                 "last_detected": None,
            #                 "alert": False,
            #                 "detected_object": copy.deepcopy(detected_object),
            #                 "polygon":detected_object
            #             }
                        
            #             # logger.debug(_id)
            #             # logger.debug(object_polygons)

            for detected_object in copy.deepcopy(data["detections"]):
                if detected_object["name"] == glb.object_class_name and detected_object["confidence"] >= 0.8:
                    x1, y1 = detected_object["x1"], detected_object["y1"]
                    x2, y2 = detected_object["x2"], detected_object["y2"]
                    x3, y3 = detected_object["x3"], detected_object["y3"]
                    x4, y4 = detected_object["x4"], detected_object["y4"]

                    detected_polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

                    x_coordinate = (detected_object["x1"] + detected_object["x2"]) // 2
                    y_coordinate = (detected_object["y1"] + detected_object["y4"]) // 2
                    centroid = Point(x_coordinate, y_coordinate)


                    for _id in loaded_camera:
                        object_id = "{}_{}_{}".format(
                            source_details["source_id"],
                            glb.sources_list[_id]["roi"]["roi_name"],
                            detected_object["object_id"],
                        )

                        # logger.debug(object_id)

                        object_polygons[object_id] = {
                            "index": _id,
                            "name": detected_object["name"],
                            "last_detected": None,
                            "created": utc_now,
                            "alert": False,
                            "detected_object": copy.deepcopy(detected_object),
                            "polygon": detected_polygon,
                        }

                        # if not glb.polygons[_id].contains(detected_polygon):
                        #     if self.object_tracker[object_id]["alert"] and self.object_tracker["roi_polygon"] == glb.polygons[_id]:
                        #         logger.debug(glb.polygons[_id].contains(detected_polygon))

                        # if not glb.polygons[_id].contains(detected_polygon):
                        # if not glb.polygons[_id].contains(centroid):

                        
                        # if not centroid.within(glb.polygons[_id]):
                        #     if object_id in self.object_tracker:
                        #         if self.object_tracker[object_id]["missing"]:
                        #             # Skip the block if 'missing' is True
                        #             pass
                        #         elif self.object_tracker[object_id]["alert"] and self.object_tracker[object_id]["roi_polygon"] == glb.polygons[_id]:
                        #             if not self.object_tracker[object_id]["missing"]:
                        #                 self.object_tracker[object_id]["missing"] = True
                        #                 logger.debug(self.object_tracker[object_id]["missing"])
                        #                 compliance_check_info[object_id] = {
                        #                     "object_id": object_id,
                        #                     "object_metadata": object_polygons[object_id]["detected_object"],
                        #                     "source_details": SourceDetails(
                        #                         **glb.sources_list[int(object_polygons[object_id]["index"])][
                        #                             "source"
                        #                         ].logs_payload()
                        #                     ),
                        #                     "user_data": glb.sources_list[int(object_polygons[object_id]["index"])][
                        #                         "user"
                        #                     ],
                        #                     "roi_details": copy.deepcopy(
                        #                         glb.sources_list[int(object_polygons[object_id]["index"])]["roi"]
                        #                     ),
                        #                     "roi_name": glb.sources_list[_id]["roi"]["roi_name"],
                        #                     "area": "patient detection in region {}".format(
                        #                         glb.sources_list[_id]["roi"]["roi_name"]
                        #                     ),
                        #                 }
                        #                     # "vanished": datetime.datetime.utcnow,

                        #                 # logger.debug(compliance_check_info[object_id]["vanished"])

                        #                 self.post_process(
                        #                     object_id = object_id,
                        #                     storage_path=self.image_storage_path,
                        #                     compliance_check_info=copy.deepcopy(compliance_check_info),
                        #                     alert_schema=copy.deepcopy(self.alert_metadata),
                        #                     index=_id,
                        #                     detected_object=copy.deepcopy(detected_object),
                        #                     key=key,
                        #                     headers=source_details,
                        #                     transaction_id=transaction_id,
                        #                     alert_text="Patient not present in region {}",
                        #                     **data,
                        #                 )

                        if glb.polygons[_id].contains(detected_polygon):
                            if object_id not in self.object_tracker:
                                self.object_tracker[object_id] = {
                                    "last_detected": None,
                                    "created": utc_now,
                                    "alert": False,
                                    "detected_object": copy.deepcopy(detected_object),
                                    "polygon": detected_polygon,
                                    "roi_polygon": glb.polygons[_id],
                                    "missing": False,
                                }

                            if self.object_tracker[object_id]["alert"]:
                                if self.object_tracker[object_id]['last_detected']:
                                    
                                    glb.sample_generator[object_id] = self.object_tracker[object_id]
                                    self.object_tracker[object_id]["last_detected"] = utc_now

                            if not self.object_tracker[object_id]["alert"]:
                                time_diff = (utc_now - self.object_tracker[object_id]["created"]).seconds
                                if time_diff >= 0:
                                    compliance_check_info[object_id] = {
                                        "object_id": object_id,
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
                                        "roi_name": glb.sources_list[_id]["roi"]["roi_name"],
                                        "area": "patient detection in region {}".format(
                                            glb.sources_list[_id]["roi"]["roi_name"]
                                        ),
                                    }

                                    # logger.debug(compliance_check_info[object_id]["source_details"]["source_owner"])

                                    self.object_tracker[object_id]["alert"] = True
                                    self.object_tracker[object_id]["last_detected"] = utc_now
                                    logger.debug(object_id)
                                    
                                    self.post_process(
                                        object_id = object_id,
                                        storage_path=self.image_storage_path,
                                        compliance_check_info = copy.deepcopy(compliance_check_info),
                                        alert_schema=copy.deepcopy(self.alert_metadata),
                                        index=_id,
                                        detected_object=copy.deepcopy(detected_object),
                                        key=key,
                                        headers=source_details,
                                        transaction_id=transaction_id,
                                        alert_text="patient detection in region {}",
                                        **data,
                                    )

                        if not glb.polygons[_id].contains(detected_polygon):
                            if object_id in self.object_tracker:
                                if self.object_tracker[object_id]["missing"]:
                                    pass

                                elif self.object_tracker[object_id]["alert"] and self.object_tracker[object_id]["roi_polygon"] == glb.polygons[_id]:
                                    if not self.object_tracker[object_id]["missing"]:
                                        self.object_tracker[object_id]["missing"] = True
                                        logger.debug(self.object_tracker[object_id]["missing"])
                                        compliance_check_info[object_id] = {
                                            "object_id": object_id,
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

                                        logger.debug(compliance_check_info[object_id]["vanished"])
                                        
                                        self.post_process(
                                            object_id = object_id,
                                            storage_path=self.image_storage_path,
                                            compliance_check_info = copy.deepcopy(compliance_check_info),
                                            alert_schema=copy.deepcopy(self.alert_metadata),
                                            index=_id,
                                            detected_object=copy.deepcopy(detected_object),
                                            key=key,
                                            headers=source_details,
                                            transaction_id=transaction_id,
                                            alert_text="AHHHHHHHHHHH {}",
                                            **data,
                                        )                        
                                
        except Exception as e:
            logger.error(
            "Error on line {}  EXCEPTION: {}".format(sys.exc_info()[-1].tb_lineno, e)
        )


logicHandler = LogicHandler()


# # Loop over the loaded camera indexes
# for _id in glb.loaded_camera_ids[source_details["source_id"]]["indexes"]:
#     object_id_found = False  # Flag to indicate if any object is detected in the ROI

#     # Get the polygon corresponding to the current index
#     current_polygon = glb.polygons[_id]

#     # Check if the detected object is within the current polygon
#     if current_polygon.contains(detected_polygon):
#         object_id_found = True  # Set the flag to True as object is detected in the ROI
#         break  # No need to check further as object is found in this ROI

# # Check if no object is detected in the current ROI
# if not object_id_found:
#     print("No objects detected in the current ROI")
