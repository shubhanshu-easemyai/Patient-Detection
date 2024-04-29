from shapely.geometry import Polygon, Point
# import requests
import sys

from core.database_handler.models import *
from core.rdx_connection_handler import *
import core.globals as glb


def fetch_default_settings(width, height):
    return {
        "ROI_settings": [
            {
                "roi_name": "roi1",
                "cords": {
                    "x1": 0,
                    "x2": width,
                    "x3": width,
                    "x4": 0,
                    "y1": 0,
                    "y2": 0,
                    "y3": height,
                    "y4": height,
                },
                "loi": [],
            }
        ],
    }


def load_configuration_settings(source_id, source_name, **kwargs):
    try:
        source_info = SourceInfo.objects(
            source_id=source_id, source_name=source_name
        ).get()
        if source_id not in glb.loaded_camera_ids:
            glb.loaded_camera_ids[source_id] = {
                "source_name": source_name,
                "indexes": [],
                "extra":{}
            }
        else:
            removed_items = 0
            first_index = 0
            for _id, _index in enumerate(glb.loaded_camera_ids[source_id]["indexes"]):
                if _id == 0:
                    first_index = _index
                glb.polygons.pop(_index - _id)
                glb.sources_list.pop(_index - _id)
                removed_items += 1
            if removed_items != 0:
                for _source in glb.loaded_camera_ids:
                    glb.loaded_camera_ids[_source]["indexes"] = [
                        x - removed_items if x >= first_index else x
                        for x in glb.loaded_camera_ids[_source]["indexes"]
                    ]

            glb.loaded_camera_ids[source_id]["indexes"] = []
    except DoesNotExist:
        return

    usecase_settings = UsecaseParameters.objects(source_details=source_info).all()
    # logger.info(usecase_settings)

    start_index = len(glb.sources_list)

    try:
        for settings in usecase_settings:
            # logger.info(settings.id)
            for roi in settings.settings["ROI_settings"]:
                corners = []

                for i in range(int(len(roi["cords"].keys()) / 2)):
                    corners.append(
                        (
                            int(roi["cords"]["x{}".format(i + 1)]),
                            int(roi["cords"]["y{}".format(i + 1)]),
                        )
                    )

                glb.polygons.append(Polygon(corners))
                glb.sources_list.append(
                    {
                        "max_time_threshold": int(
                            roi.get("max_time_threshold", glb.max_time_threshold)
                        ),
                        "source": settings.source_details,
                        "user": settings.user_details,
                        "roi": {"cords": roi["cords"], "roi_name": roi["roi_name"]},
                        "source_name": settings.source_details.source_name,
                        "source_id": source_id
                    }
                )
                glb.max_time_threshold = int(
                    roi.get("max_time_threshold", glb.max_time_threshold)
                )
                glb.loaded_camera_ids[source_id]["indexes"].append(start_index)
                glb.loaded_camera_ids[source_id]["indexes"] = list(
                    set(glb.loaded_camera_ids[source_id]["indexes"])
                )
                glb.loaded_camera_ids[source_id]["extra"][start_index] = {
                    "max_time_threshold": int(
                        roi.get("max_time_threshold", glb.max_time_threshold)
                    ),
                    "source": settings.source_details,
                    "user": settings.user_details,
                    "roi": {"cords": roi["cords"], "roi_name": roi["roi_name"]},
                    "source_name": settings.source_details.source_name,
                    "source_id": source_id
                }
                start_index += 1
            
    except Exception as e:
        logger.debug(e)
        glb.sources_list = []
    # logger.info(glb.sources_list)
    # logger.info(glb.loaded_camera_ids)
    # logger.info(glb.polygons)
