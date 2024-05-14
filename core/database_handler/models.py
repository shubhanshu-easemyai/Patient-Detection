from mongoengine import *
import datetime
import copy


class SourceInfo(Document):
    source_id = StringField(required=True, unique=True)
    source_type = StringField()
    source_subtype = StringField()
    source_url = StringField()
    source_location_name = StringField()
    source_glocation_coordinates = ListField(StringField())
    source_frame_width = IntField()
    source_frame_hight = IntField()
    source_owner = StringField()
    source_name = StringField(required=True, unique=True)
    source_tags = ListField(StringField())
    resolution = ListField(IntField())

    def payload(self, user_details: dict = {}):
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_subtype": self.source_subtype,
            "resolution": self.resolution,
            "source_owner": user_details
        }

    def logs_payload(self):
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_owner": self.source_owner
        }


class UserInfo(Document):
    user_id = StringField(required=True)
    username = StringField()
    user_type = StringField(default="owner")
    access_key = StringField()

    def payload(self):
        return {
            "user_id": self.user_id,
            "username": self.username
        }


class UsecaseParameters(Document):
    source_details = ReferenceField(SourceInfo)
    user_details = ReferenceField(UserInfo)
    settings = DictField()
    created = DateTimeField(default=datetime.datetime.utcnow)



class GeneralSettings(Document):
    output_name = StringField()
    user_details = ReferenceField(UserInfo)
    settings = DictField()


class UserSessions(Document):
    widget_name = StringField(required=True)
    widget_id = StringField()
    user_data = ReferenceField(UserInfo)
    user_inputs = DictField()
    widget_data = DictField()
    timezone = StringField()
    last_updated = DateTimeField(default=datetime.datetime.utcnow)

    def payload(self):
        return {
            "widget_name": self.widget_name,
            "widget_id": self.widget_id,
            "widget_data": self.widget_data,
            "user_inputs": self.user_inputs,
            "user_data": self.user_data,
            "timezone": self.timezone,
            "last_updated": "{}Z".format(
                self.last_updated if self.last_updated else datetime.datetime.utcnow()
            ),
        }
    
class SourceDetails(EmbeddedDocument):
    source_name = StringField()
    source_id = StringField()
    source_owner = StringField()
    
class DetectionLogs(Document):
    source_details = EmbeddedDocumentField(SourceDetails)
    user_data = ReferenceField(UserInfo)
    object_metadata = DictField()
    roi_details = DictField()
    object_id = StringField()
    image_url = StringField()
    image_height = IntField()
    image_width = IntField()
    created = DateTimeField(default=datetime.datetime.utcnow)
    vanished = DateTimeField(null=True)
    area = StringField()
    roi_name = StringField()
    meta = {
        "strict": False,
        "indexes": [
            "created",
            "source_details.source_name",
            "source_details.source_id",
            "source_details.source_owner",
        ],
    }

    def payload(self):
        _object_metadata = copy.deepcopy(self.object_metadata)
        return {
            "source_name": self.source_details.source_name,
            "metadata": [{
                "object_id": self.object_id,
                "media_link": self.image_url,
                "media_type":   "image",
                "media_height": self.image_height,
                "media_width": self.image_width,
                "roi_details": self.roi_details,
                "detections": [{
                    "confidence": _object_metadata.pop(
                        "confidence"
                    ),
                    "name": _object_metadata.pop("name"),
                    "object_id": _object_metadata.pop(
                        "object_id"
                    ),
                    "bounding_box": _object_metadata,
                }],
            }],
            "created": "{}Z".format(self.created),
            "vanished": "{}Z".format(self.vanished)
        } 
