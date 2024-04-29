from core.database_handler.models import *
import core.globals as glb
from core.utils import fetch_default_settings


def get_configuration_settings(source_info, user_details, **kwds):
    usecase_parameters = UsecaseParameters.objects.get(
        source_details=source_info, user_details=user_details
    )
    keys_to_extract = ["ROI_settings"]
    return dict(
        filter(
            lambda item: item[0] in keys_to_extract, usecase_parameters.settings.items()
        )
    )


def post_configuration_settings(settings, source_info, user_details, **kwds):
    usecase_parameters = UsecaseParameters.objects.get(
        source_details=source_info, user_details=user_details
    )
    usecase_parameters.settings["ROI_settings"] = settings["ROI_settings"]
    usecase_parameters.save()

    return {"detail": "success"}


def reset_configuration_settings(source_info, user_details, **kwds):
    usecase_parameters = UsecaseParameters.objects.get(
        source_details=source_info, user_details=user_details
    )
    usecase_parameters.settings["ROI_settings"] = fetch_default_settings(
        source_info.resolution[0],
        source_info.resolution[1],
    )["ROI_settings"]
    usecase_parameters.save()

    return {"detail": "success"}
