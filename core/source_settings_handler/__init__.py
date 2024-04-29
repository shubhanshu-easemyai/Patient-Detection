from typing import Any
from mongoengine.errors import *
import copy

from core.database_handler.models import *
from core.rdx_connection_handler import *
from core.utils import * 


class AppSourceSettingsHandler:
    def __init__(self) -> None:
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        func_name = "{}_settings".format(kwds["type"])
        if hasattr(self, func_name) and callable(func := getattr(self, func_name)):
            try:
                func(**kwds)
            except Exception as e:
                logger.debug(e)

    def link_source_settings(self, sources: dict, users: dict, **kwargs):
        for group_name, group_sources in sources.items():
            for source_details in group_sources:
                try:
                    logger.debug(users["user_id"])
                    source_info = SourceInfo.objects.get(
                        source_id=source_details["source_id"]
                    )
                    source_info.source_owner = users["user_id"]
                    logger.debug(source_info["source_owner"])
                except DoesNotExist:
                    logger.debug(users["user_id"])
                    source_info = SourceInfo(**source_details)
                    source_info.source_owner = users["user_id"]
                    logger.debug(source_info["source_owner"])
                    source_info.save()

                _source_details = {}
                for k, v in source_details.items():
                    if k != "source_id":
                        _source_details["set__{}".format(k)] = v
                source_info.update(**_source_details)

                try:
                    user_details = UserInfo.objects.get(user_id=users["user_id"])
                except DoesNotExist:
                    user_details = UserInfo(**users)
                    user_details.save()

                try:
                    usecase_parameters = UsecaseParameters.objects.get(
                        source_details=source_info, user_details=user_details
                    )
                    usecase_parameters.settings = (
                        kwargs["settings"]
                        if "settings" in kwargs
                        else fetch_default_settings(
                            source_details["resolution"][0],
                            source_details["resolution"][1],
                        )
                    )
                except DoesNotExist:
                    usecase_parameters = UsecaseParameters(
                        source_details=source_info,
                        user_details=user_details,
                        settings=(
                            kwargs["settings"]
                            if "settings" in kwargs
                            else fetch_default_settings(
                                source_details["resolution"][0],
                                source_details["resolution"][1],
                            )
                        ),
                    )

                usecase_parameters.save()
                load_configuration_settings(**source_info.payload())
        return "success"

    def unlink_source_settings(self, sources: dict, users: dict, **kwargs):
        try:
            for group_name, group_sources in sources.items():
                for source_details in group_sources:
                    source_info = SourceInfo.objects.get(
                        source_id=source_details["source_id"]
                    )
                    user_info = UserInfo.objects.get(user_id=users["user_id"])

                    usecase_parameters = UsecaseParameters.objects.get(
                        source_details=source_info, user_details=user_info
                    )
                    usecase_parameters.delete()
                    load_configuration_settings(**source_info.payload())
            return "success"
        except DoesNotExist:
            pass

    def update_source_settings(self, sources: dict, users: dict, **kwargs):
        new_resolution = []
        prev_resolution = []
        try:
            for group_name, group_sources in sources.items():
                for source_details in group_sources:
                    _source_details = {}
                    for k, v in source_details.items():
                        _source_details["set__{}".format(k)] = v
                        if k == "resolution":
                            new_resolution = copy.deepcopy(v)

                    source_info = SourceInfo.objects.get(
                        source_id=source_details["source_id"]
                    )
                    prev_resolution = copy.deepcopy(source_info.resolution)
                    source_info.update(**_source_details)

                    user_details = UserInfo.objects.get(user_id=users["user_id"])

                    if (
                        new_resolution[0] != prev_resolution[0]
                        or new_resolution[1] != prev_resolution[1]
                    ):
                        usecase_parameters = UsecaseParameters.objects.get(
                            source_details=source_info, user_details=user_details
                        )

                        updated_roi_settings = []
                        for roi_settings in usecase_parameters.settings["ROI_settings"]:
                            for k, v in roi_settings["cords"].items():
                                if k.count("x") != 0:
                                    roi_settings["cords"][k] = int(
                                        v / prev_resolution[0] * new_resolution[0]
                                    )
                                else:
                                    roi_settings["cords"][k] = int(
                                        v / prev_resolution[1] * new_resolution[1]
                                    )
                            updated_roi_settings.append(copy.deepcopy(roi_settings))
                        usecase_parameters.settings["ROI_settings"] = (
                            updated_roi_settings
                        )
                        usecase_parameters.save()

                    load_configuration_settings(**source_info.payload())
            return "success"
        except DoesNotExist:
            pass
