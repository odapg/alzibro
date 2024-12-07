#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import json
import zipfile
import os
import sys
import subprocess

from alfred import item_variables, enter_mods, base_item, selection_error_message, FOLDER_ICON

# ---------------------------------- Path functions -----------------------------------#

def list_paths(zip_file):
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            paths = zip_ref.namelist()
            # In some rare cases, .namelist() generates paths with carriage returns
            # --- better skip them
            cleaned_paths = [p for p in paths if not "\r" in p]
            return cleaned_paths
    except Exception as e:
        comment = f"Error when opening '{os.path.basename(zip_file)}'" 
        subcomment = str(e)
        selection_error_message(comment, subcomment)
        sys.exit()

def sort_paths_by_depth_and_name(paths):
    # sorts by depth, then directories first/files second, and then alphabetically
    # (with files not beginning with '.' first)
    return sorted(paths, key=lambda x: (x.count('/') - x.endswith('/'), not x.endswith('/'), 
                    os.path.basename(x.rstrip('/')).startswith('.'),  x))

def filter_macosx_paths(paths):
    return [f for f in paths if not f.startswith('__MACOSX')]

def filter_dsstore_paths(paths):
    return [f for f in paths if '.DS_Store' not in f]

def filter_directories_only(paths):
    return [f for f in paths if f.endswith('/')]

def filter_files_only(paths):
    return [f for f in paths if not f.endswith('/')]

def filter_paths_in_directory(paths, directory, show_subfolder_contents):
    filtered_paths= [f for f in paths 
        if f.startswith(directory)
        and f != directory
        and (f.lstrip(directory).rstrip('/').count('/') == 0 or show_subfolder_contents == "1")
    ]
    # Some ZIP files have files the main directory not listed in the namelist
    if directory == "" and not filtered_paths:
        filtered_paths= [f for f in paths 
        if f.startswith(directory)
        and f != directory
        and (f.lstrip(directory).rstrip('/').count('/') == 1 or show_subfolder_contents == "1")
    ]    
    return filtered_paths

def parent_path(my_path):
    # gives the parent path to go to after ⇧↩ — with a particular form for short paths
    my_path = my_path.rstrip('/')
    parts = my_path.split('/')
    if len(parts)<=1:
        return ""
    else:
        return '/'.join(parts[:-1]) +'/'

# ------------------------------ JSON items makers -------------------------------#
'''
For the following three add_to_JSON functions:
 json_list = the list that will produce the JSON output, in its current state
 zip_file = the processed .zip file 
 current_directory = the folder that is currently under view
 my_path = the path for the file or folder under view (which may be in a subfolder)
 return_to_unzip = for a file, indicates if ↩ should directly extract it
'''

def add_folder_to_JSON(json_list, my_path, current_directory):
    # JSON entry if the considered path corresponds to a nonempty folder
    
    title = os.path.basename(my_path.rstrip('/'))
    subtitle ="🗃/" + my_path
    icon = FOLDER_ICON
    variables = item_variables(my_path, do_extraction=False) 
    parent_directory = parent_path(current_directory)
    hint="Hit ↩ to open the folder, ⇧↩ to go to the parent folder, ⌘↩ to unzip"

    new_item =  base_item(title, subtitle, variables, icon, is_valid=True)

    my_mods = {}
    variables = item_variables(parent_directory, do_extraction=False)
    enter_mods("shift", f"← Go to the parent folder", variables, True, my_mods)
    variables = item_variables(current_directory, do_extraction=True, file_to_extract=my_path)
    enter_mods("cmd", f"Extract this folder", variables, True, my_mods)
    variables = item_variables("", do_extraction=False)
    enter_mods("alt", hint, variables, False, my_mods)
    enter_mods("ctrl", hint, variables, False, my_mods)

    new_item.update({"mods" :my_mods})

    json_list["items"].append(new_item)
    return 

#--------------------

def add_file_to_JSON(json_list, my_path, current_directory, return_to_unzip):
    # JSON entry if the considered path corresponds to a file

    title = os.path.basename(my_path)
    subtitle ="🗃/" + my_path
    icon = "file_icon.png"
    if return_to_unzip == "1":
        do_extraction = True
    else:
        do_extraction = False
    variables = item_variables(current_directory, do_extraction, my_path),
    parent_directory = parent_path(current_directory)
    if return_to_unzip:
        hint="Hit ⇧↩ to go to the parent folder, ↩ or ⌘↩ to unzip"
    else:
        hint="Hit ⇧↩ to go to the parent folder, ⌘↩ to unzip"
    
    new_item =  base_item(title, subtitle, variables, icon, is_valid=do_extraction)

    my_mods = {}
    variables = item_variables(parent_directory, do_extraction=False)
    enter_mods("shift", f"← Go to the parent folder", variables, True, my_mods)
    variables = item_variables(current_directory, do_extraction=True, file_to_extract=my_path)
    enter_mods("cmd", f"Extract this file", variables, True, my_mods)
    variables = item_variables(current_directory, do_extraction=False, file_to_extract=my_path)
    enter_mods("ctrl", f"Take a Quicklook at this file", variables, True, my_mods)
    variables = item_variables("", do_extraction=False)
    enter_mods("alt", hint, variables, False, my_mods)

    new_item.update({"mods" :my_mods})

    json_list["items"].append(new_item)
    return 

#--------------------

def JSON_if_empty_directory(json_list, current_directory):
    # JSON entry if the considered path corresponds to an empty directory

    title = "This directory is empty"
    subtitle = "Hit ⇧↩ to go to the parent folder"
    variables = item_variables(current_directory, False)
    icon = "empty_set.png"
    parent_directory = parent_path(current_directory)
    hint = subtitle

    new_item =  base_item(title, subtitle, variables, icon, is_valid=False)

    my_mods = {}
    variables = item_variables(parent_directory, do_extraction=False)
    enter_mods("shift", f"← Go to the parent folder", variables, True, my_mods)
    variables = item_variables("", do_extraction=False)
    enter_mods("alt", hint, variables, False, my_mods)
    enter_mods("ctrl", hint, variables, False, my_mods)
    enter_mods("cmd", hint, variables, False, my_mods)

    new_item.update({"mods" :my_mods})

    json_list["items"].append(new_item)
    return 

#-------------------------------- ZIP & Cache  ----------------------------------#

def manage_cache_cleaner(cache_folder):
    # If the cache cleaner process exists, renew its timeout, otherwise create it
    cache_file = os.path.join(cache_folder, 'alzibro_cache')
    cache_pid_file = os.path.join(cache_folder, 'cache_script.pid')
    if os.path.isfile(cache_pid_file):
        with open(cache_pid_file) as file:
            pid = int(file.readline())
    else:
        pid=-1
    # Check if this pid corresponds to alzibro_cache_cleaner
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if "alzibro_cache_cleaner" in result.stdout:
        subprocess.Popen(f"kill -USR1 {pid} &", shell=True, 
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen("zsh ./alzibro_cache_cleaner.sh &", shell=True, 
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return

#--------------------

def read_and_cache_zipfile(zip_file, cache_folder, cache_file):
    # Reads the zip file, caches the paths in it in alzibro_cache_file,
    # and returns a list of these paths

    paths = list_paths(zip_file)
        
    if not os.path.isdir(cache_folder):
        try:
            os.mkdir(cache_folder)
        except Exception as e:
            comment = f"Error creating cache folder" 
            subcomment = str(e)
            selection_error_message(comment, subcomment)
            sys.exit()
    try:
        with open(cache_file,'w') as file:
            file.write('\n'.join(paths))
    except Exception as e:
        comment = f"Error writing cache file" 
        subcomment = str(e)
        selection_error_message(comment, subcomment)
        sys.exit()

    return paths

# ------------------------------------- MAIN -------------------------------------#

def main():

    # Calling Variables
    starting = os.getenv('starting')
    zip_file = os.getenv('zip_file')
    if zip_file == None: zip_file=os.getenv('opened_zipfile')
    current_directory = os.getenv('next_directory')
    if not current_directory or current_directory == "/": current_directory = ""
    return_to_unzip = os.getenv('return_to_unzip_files')
    show_subfolder_contents = os.getenv('show_subfolder_contents')
    cache_folder = os.getenv('alfred_workflow_cache')
    cache_file = os.path.join(cache_folder, 'alzibro_cache')
    clear_cache = os.getenv('clear_cache')   

    # Gathering the paths from either the zip file or the cache
    if starting=="1":
        paths = read_and_cache_zipfile(zip_file, cache_folder, cache_file)     
    else:
        try:
            with open(cache_file,'r') as file:
                paths = [line.rstrip() for line in file]
        except Exception as e:
            paths = read_and_cache_zipfile(cache_folder, cache_file)

    # If the option is set, runs or resets the cache cleaner script
    if clear_cache == "1":
        manage_cache_cleaner(cache_folder)
    
    # Filtering and sorting the paths
    paths = filter_macosx_paths(paths)
    paths = filter_dsstore_paths(paths)
    paths = filter_paths_in_directory(paths, current_directory, show_subfolder_contents)

    if show_subfolder_contents == "1":
        all_paths = filter_directories_only(paths) + filter_files_only(paths)
        sorted_paths = sort_paths_by_depth_and_name(all_paths)
    else:
        sorted_folder_paths = sort_paths_by_depth_and_name(filter_directories_only(paths))
        sorted_file_paths = sort_paths_by_depth_and_name(filter_files_only(paths))
        sorted_paths = sorted_folder_paths + sorted_file_paths

    resultJSON = {"items": []} 

    # If one wants to limit entries for speed purposes
    # Set an environment variable 'alzibro_items_limit' and uncomment the two following lines
    #
    # alzibro_items_limit = int(os.getenv('alzibro_items_limit')) 
    # sorted_paths = sorted_paths[:alzibro_items_limit]
    
    # Generating the Alfred JSON output
    if sorted_paths:
        for my_path in sorted_paths:
            if my_path.endswith('/'):
                add_folder_to_JSON(resultJSON, my_path, current_directory)
            else:
                add_file_to_JSON(resultJSON, my_path, current_directory, return_to_unzip)
    else:
        JSON_if_empty_directory(resultJSON, current_directory)
    
    print(json.dumps(resultJSON))


#--------------------
    
if __name__ == "__main__":
    main()
