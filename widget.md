"app_data": {
     "$oid": "6629f1da78337590ad14dd51"
}, make this app_data Object_id equal to the app_data of the app in widget_management_db.app_configuration_settings 

[{
    "_id": {
      "$oid": "6602aaea005263fb79b1094a"
    },
    "widget_name": "live_alerts",
    "app_data": {
      "$oid": "6629f1da78337590ad14dd51"
    },
    "settings": {
      "id": "6602aaea005263fb79b1094a",
      "label": "Live Alerts",
      "properties": {
        "filter": {
          "id": "camera_name_dropdown",
          "component_name": "Dropdown",
          "properties": {
            "multiselect": true,
            "placeholder": "select camera",
            "options": [],
            "icon": null
          },
          "style": {
            "width": "100%"
          },
          "events": {
            "onLoad": {
              "type": "socket"
            },
            "onClick": {
              "type": "socket"
            }
          }
        },
        "sort_by": {},
        "content": {
          "id": "live_alerts",
          "properties": {
            "rows": [
              {
                "columns": [
                  {
                    "id": "alert_table",
                    "component_name": "Table",
                    "properties": {
                      "headers": [
                        {
                          "id": "images",
                          "component_name": "Text",
                          "label": "Images"
                        },
                        {
                          "id": "camera",
                          "component_name": "Text",
                          "label": "Camera Name"
                        },
                        {
                          "id": "alert",
                          "component_name": "Text",
                          "label": "Alert"
                        },
                        {
                          "id": "priority",
                          "component_name": "Text",
                          "label": "Priority"
                        },
                        {
                          "id": "date",
                          "component_name": "Text",
                          "label": "Date"
                        },
                        {
                          "id": "time",
                          "component_name": "Text",
                          "label": "Time"
                        }
                      ],
                      "columns": [
                        {
                          "id": "images",
                          "component_name": "Images",
                          "properties": {}
                        },
                        {
                          "id": "camera",
                          "component_name": "Text",
                          "properties": {},
                          "style": {
                            "color": "#01C744"
                          }
                        },
                        {
                          "id": "alert",
                          "component_name": "Tag",
                          "properties": {},
                          "style": {
                            "color": "#3A62FF"
                          }
                        },
                        {
                          "id": "priority",
                          "component_name": "Tag",
                          "properties": {},
                          "style": {
                            "color": "#FF9900"
                          }
                        },
                        {
                          "id": "date",
                          "component_name": "Text",
                          "properties": {
                            "format": "DD/MM/YYYY"
                          }
                        },
                        {
                          "id": "time",
                          "component_name": "Text",
                          "properties": {
                            "format": "HH:MM:SS",
                            "hour12": true
                          }
                        }
                      ]
                    }
                  }
                ]
              }
            ]
          }
        }
      }
    },
    "created": {
      "$date": "2024-03-20T07:40:04.572Z"
    },
    "widget_info": "this widget will show the real time alerts generated in system",
    "widget_thumbnail": "/static_server/app_media/alert_management/Custom_Data/widgets/thumbnail/alert_logs.png",
    "size": {
      "w": 6,
      "h": 6,
      "minW": 6,
      "minH": 6
    }
  }]