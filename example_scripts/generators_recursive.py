#!/usr/bin/python

'''
create a regular dictionary from a nested dictionary
'''

def _nested_objects(test_dict):
    for key, value in test_dict.items():
        if type(value) is dict:
            yield _nested_objects(value)
        else:
            yield (key, value)

# get the desired result dictionary from any form of  a nested dictionary
def _objects(test_dict):
        result_dict = {}
        # get the first generator object called items
        for items in _nested_objects(test_dict):
            # assign values to result dict belonging to the first generator object
            if type(items) is tuple:
                result_dict[items[0]] = items[1]

            else:
                # walk through the generator objects and assign all other values to result dict
                for item in items:
                    result_dict[item[0]] = item[1]

        return result_dict

if __name__ == '__main__':

    test_dict = {   "route_guidance":
                                {
                                "BTN_Setup_Guidance": "ListItem_GuidanceSettings",
                                 "BTN_Traffic_Signs": "ListItem_ShowTrafficSigns",
                                "NAV_SETUP_GUIDANCE": "NAV2_SETUP_GUIDANCE",
                                "BTN_Consider_Trailer": "ListItem_DetectTrailer",
                                "DD_SPEEDLIMIT_TRESHOLD": "ListItem_SpeedLimitWarning_TabBar",
                                "SLIDER_DD_SPEEDLIMIT": "ListItem_SpeedLimitWarning_TabBar.Container_Slider",
                                "BTN_Detect_Trailer": "ListItem_DetectTrailer",
                                "BTN_Trailer_Speed": "ListItem_TrailerSpeed_TabBar",
                                "SLIDER_Trailer_Speed": "ListItem_TrailerSpeed_TabBar.Container_Slider",
                                "DD_SPEED_WARNING": "ListItem_SpeedWarning",
                                },
                        "voice_guidance":
                                {
                                "BTN_Setup_Audio": "ListItem_AudioSettings",
                                "BTN_Mute_voice_toggle": "ListItem_NavigationAnnouncements",
                                "DD_NAV_Announcement_typ": "ListItem_VoiceAnnouncement",
                                "DD_NAV_Announcement_During_Calls": "ListItem_VoiceAnnouncementsDuringCalls",
                                "NAV_SETUP_AUDIO": "NAV2_SETUP_AUDIO",
                                "DD_ENT_Volume": "ListItem_EntertainmentLowering_TabBar",
                                "DD_NAV_Volume": "ListItem_NavVolume_TabBar",
                                "SLIDER_DD_ENT_Volume": "ListItem_EntertainmentLowering_TabBar.Container_Slider",
                                "SLIDER_DD_NAV_Volume": "ListItem_NavVolume_TabBar.Container_Slider",
                                },
                        "database_setup":
                                {
                                "BTN_Setup_Database": "ListItem_DatabaseInformation",
                                "NAV_SETUP_DATABASE": "NAV2_SETUP_DATABASE",
                                },
                        "basic_settings":
                                {
                                "BTN_Setup_Basic": "ListItem_AdvancedSettings",
                                "NAV_SETUP_BASIC": "NAV2_SETUP_ADVANCED",
                                },
        # all other items
        "NAV_SETUP": "NAV2_SETUP_MAIN",
    }

    result_dict = _objects(test_dict)
    
    print(result_dict)


