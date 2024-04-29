from core.database_handler.models import *
import core.globals as glb


def get_general_settings(user_details, **kwds):
    response = {}
    general_settings = GeneralSettings.objects(
        user_details=user_details
    ).all()

    for settings in general_settings:
        response.update({settings.output_name: settings.settings})

    if "alert_interval" not in response:
        response["alert_interval"] = {"interval": glb.max_time_threshold}
        response["include_head"] = {
            "status": "True" if glb.include_head else "False"
        }

    return response


def post_general_settings(settings, user_details, **kwds):
    for output_name, setting in settings.items(): 
        general_settings = GeneralSettings.objects(
            user_details=user_details, output_name=output_name
        ).first()
        if not general_settings:
            general_settings = GeneralSettings(
                user_details=user_details, output_name=output_name
            )

        if isinstance(setting, dict) or isinstance(setting, list):
            general_settings.settings = setting
        elif isinstance(setting, str) or isinstance(setting, bool):
            general_settings.settings = {output_name: setting}
        general_settings.save()

        if output_name == "alert_interval":
            if "interval" in setting and setting["interval"]:
                glb.update_job(setting["interval"])
            else:
                glb.update_job(60)
        if output_name == "include_head":
            glb.include_head = (
                True if setting["status"] == "True" else False
            )

    return {"detail": "success"}


def reset_general_settings(user_details, **kwds):
    general_settings = GeneralSettings.objects.get(
                    user_details=user_details
                )
    general_settings.delete()

    return {"detail": "success"}


# def get_general_settings(user_details, **kwds):
#     response = {}
#     general_settings = GeneralSettings.objects(user_details=user_details).all()

#     for settings in general_settings:
#         response.update({settings.output_name: settings.settings})
#     return response


# def post_general_settings(settings, user_details, **kwds):
#     for output_name, setting in settings.items():
#         general_settings = GeneralSettings.objects(
#             user_details=user_details, output_name=output_name
#         ).first()
#         if not general_settings:
#             general_settings = GeneralSettings(
#                 user_details=user_details, output_name=output_name
#             )
#         general_settings.save()

#     return {"detail": "success"}


# def reset_general_settings(user_details, **kwds):
#     general_settings = GeneralSettings.objects.get(user_details=user_details)
#     general_settings.delete()

#     return {"detail": "success"}
