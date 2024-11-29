#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import json

FOLDER_ICON = "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/DocumentsFolderIcon.icns"
ALERT_ICON = "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/AlertNoteIcon.icns"

def clean_dict(my_vars):
    return {key: val for (key, val) in my_vars.items() if val is not None}

#------------------- Functions to create items in Alfred ---------------------#

def item_variables(next_directory, do_extraction=False, file_to_extract=None):
    
    my_vars = {
        "next_directory": next_directory,
        "file_to_extract": file_to_extract,
        "do_extraction": do_extraction,
    }
    return clean_dict(my_vars)

def base_item(title, subtitle, variables, icon, is_valid=True):
    my_item = {                 
        "title": title,
        "subtitle": subtitle,
        "variables": variables,
        "valid": is_valid,
        "icon": { "path": icon },
    }
    return my_item

def enter_mods(modifier, subtitle, variables, is_valid, my_mods=None):
    if my_mods == None:
        my_mods = {}
    my_vars = {
        "valid": is_valid,
        "subtitle": subtitle,
        "variables": variables
    }
    result = { modifier:  my_vars}
    my_mods.update(result)
    return

def selection_error_message(comment, subcomment):
    # Writes the errors appearing before/during the zip file browsing
    ResultJSON= {"items": [
        {"title": comment, "subtitle": subcomment, "valid": False, "icon": {"path": ALERT_ICON}}
    ] }
    print(json.dumps(ResultJSON))
    return


#-------------- Functions to pass variables after extraction ---------------#

def outcome_JSON(next_directory, comment, zip_file, to_reveal=None):
    
    my_vars = {
        "next_directory": next_directory,
        "comment": comment,
        "reveal": to_reveal,
        "opened_zipfile": zip_file,
    }
    my_vars = clean_dict(my_vars)
    ResultJSON= { "alfredworkflow": { "arg" : "", "variables": my_vars, } }
    return ResultJSON


def alfred_error_message(comment, next_directory, zip_file):
    
    ResultJSON = outcome_JSON(next_directory, comment, zip_file)
    print(json.dumps(ResultJSON))

