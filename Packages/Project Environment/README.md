# Project Environment

A plugin for **SublimeText 3** that allows to set environment variables in the .sublime-project file.  

---

## Description:

Variables set with **Project Environment** are available throughout Sublime. Builds, scripts, even other plugins can relay and use them.

The very nice thing about **Project Environment** is that all the variables it sets are set per project.  
**Project Environment** can catch when a Sublime's project change and re-set the environment variables accordingly. Even more, if you have two or more Sublime's windows open at the same time, each time you get focus on one of them, **Project Environment** will run and re-set the variables. 

All this is completely transparent to the user.

---

## Settings

there are few settings you can change in ProjectEnvironment.sublime-settings:

* **print_output**  
    When this is set to true, some informations are printed out to console.  

* **set_sublime_variables**  
    If true some variables from within Sublime will be set too  
    this variables are:  
    "project_path", "project", "project_name", "project_base_name", "packages"

* **sublime_variables_prefix**  
    It may be useful to add a prefix to those variables so that they don't conflict with yours

* **sublime_variables_capitalized**  
    Those variables can be all capitalised if you wish.  
    ex: "project" -> "PROJECT"

---

## Setup Project Variables

The variables can be set in the _"settings"_ part of a .sublime-project file.  
To avoid possible conflicts, the first thing to do is to create and new object in _"settings"_, called **"project_environment"**.

```
"settings":
{
    "project_environment":
    {
    }
}
```  

Inside _"project_environment"_ you can define 4 entries:

* **env**
* **windows**
* **osx**
* **linux**

```
"settings":
{
    "project_environment":
    {
	    "env": {},
	    "windows": {},
	    "osx": {},
	    "linux": {}
    }
}
``` 

_"env"_ is for generic, portable environment variable across different systems.   
_"windows"_, _"osx"_ and _"linux"_ are for, obviously, system specific variables.  
Please note that none of these are mandatory.
    
* **env** is a dictionary. Each `"key": "value"` pair will be set as environment variable. 
* **windows** | **osx** | **linux** are object that can contain:
    * **env**, exactly as the main *env*, but for system specific variables
    * **env_file** is a path that point to an external command file. If this file sets variables, those variables will be set also in Sublime.  
        The path can be relative to the project file itself (ex: "../../env.sh")

**Note:**  
The variables in **env_file** are always set first. This means that **env** can potentially override what **env_file** did.

This is an example of a project file:

``` json
{
    "folders":
    [
        {
            "path": "."
        }
    ],
    "settings":
    {
        "project_environment":
        {
            "print_output": true,
            "set_sublime_variables": true,
            "sublime_variables_prefix": "sublime_",
            "sublime_variables_capitalized": true,
            "env":
            {
                "CROSS_PLATFORM_ENV": "cross_platform_env"
            },
            "windows":
            {
                "env":
                {
                    "IN_LINE_ENV": "in_line_env_window"
                },
                "env_file": "./env_tests/env_test.bat"
            },
            "osx":
            {
                "env":
                {
                    "IN_LINE_ENV": "in_line_env_mac"
                },
                "env_file": "./env_tests/env_test.sh"
            },
            "linux":
            {
                "env":
                {
                    "IN_LINE_ENV": "in_line_env_linux"
                },
                "env_file": "./env_tests/env_test.sh"
            }
        }
    }
}
```

---

## Resolving Project's paths with variables

Sublime doesn't resolve variables inside project's folders paths.
To work around this limitation Project Environment allows you to define another entry
alongside a folder path, called **path_template**.  
Project Environment will resolve any environment variable in _path_template_ and replace _path_ 
with the result.

For example:

``` json
{
    "folders":
    [
        {
            "path": ".",
            "path_template": "$MY_PATH"
        }
    ],
    "settings":
    {
        "project_environment":
        {
            "windows":
            {
                "env": { "MY_PATH": "some/location/windows" }
            },
            "osx":
            {
                "env": { "MY_PATH": "some/location/mac_osx" }
            },
            "linux":
            {
                "env": { "MY_PATH": "some/location/linux" }
            }
        }
    }
}
```

When Project Environment run, automatically or calling the command **update_project_data**, _path_ will be substituted with 
the value of _MY_PATH_ and it will be a different value depending on platform running.  

**Remember**  
If _path_template_ is present, any value in _path_ will be replaced, so don't set any value in it, because it will be override. 

---

## Using the variables in a build_system

Once you have set the variables with Project Environment, you can use it in many different ways.
One common use for them is in Sublime's builds.

Imagine you have set a variable called `MY_TEST_VARIABLE` set to `Hello World!!`, then you can have:

``` json
{
	"name": "Super Test",
    "shell_cmd": "echo %MY_TEST_VARIABLE%"
}
```

In any window open in Sublime, launching the `Super Test` builder, and the result will be exactly `Hello World!!`

``` json
{
    "build_systems":
    [
        {
            "name": "Super Test",
            "shell_cmd": "echo %MY_TEST_VARIABLE%"
        }
    ],
    "folders":
    [
        {
            "path": "."
        }
    ],
    "settings":
    {
        "project_environment":
        {
            "env":
            {
                "MY_TEST_VARIABLE": "Hello World!!"
            }
        }
    }
}
```

### A small advise if you work on Linux or Mac

The example above was for Windows, you can do the same for Linux and Mac obviously, but you have to be sure you escape the variable.

``` json
{
    "build_systems":
    [
        {
            "name": "Super Test",
            "shell_cmd": "echo \\$MY_TEST_VARIABLE"
        }
    ],
    "folders":
    [
        {
            "path": "."
        }
    ],
    "settings":
    {
        "env":
        {
            "Darwin":
            {
                "MY_TEST_VARIABLE": "Hello World!!"
            }
        }
    }
}
```

Note the double backslash before `$MY_TEST_VARIABLE`. This is extremely important.
An excerpt from Sublime documentation that explains why:

> **Variables**
>
> [Sublime's] variables will be expanded within any string specified in the "cmd", "shell_cmd" or "working_dir" options.  
>
> If a literal $ needs to be specified in one of these options, it must be escaped with a `\`. Since JSON uses backslashes for escaping also, $ will need to be written as `\\$`

---

## How Project Environment collect variables from a command file

When the path to a command file (.bat, .sh, etc) is assigned to **env_file**, the plugin will run it in a child process\*. 

It will then collect all the environment variables in that child process 
and return them to the main process where the new variables, or the variables that have a different values, will be 
appended to the main environment.  

\**(using python's subprocess.Popen, with shell=False)*.
 
---

## Installation

#### Using Package Control:

Go to Preferences -> Package Control -> Install Package then type into the text-box "Project Environment"

Click on it, the package will be installed and ready for use.

#### Using Git:

Locate your Sublime Text Packages directory by using the menu item Preferences -> Browse Packages.
  
While inside the Packages directory, clone Project Environment in it:  
`git clone https://bitbucket.org/daniele-niero/sublimeprojectenvironment`
