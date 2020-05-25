import os
import sys
import json
import copy
import subprocess
import datetime
import sublime, sublime_plugin


#----------------------------------------------------#
#  Ensure we keep a copy of the default environment
#----------------------------------------------------#
DEFAULT_ENV = {}

# this is fired only once when the plugin gets loaded
def plugin_loaded():
    global DEFAULT_ENV
    DEFAULT_ENV.clear()
    DEFAULT_ENV.update(os.environ)

def to_default_environment():
    os.environ.clear()
    os.environ.update(DEFAULT_ENV)
#----------------------------------------------------#

def combine_dicts(dicta, dictb):
    updated = copy.deepcopy(dicta)
    for k2, v2 in dictb.items():
        updated[k2] = copy.deepcopy(v2)
    return updated


def pretty_print_dict(d, out_callback=sys.stdout.write):
    max_key_length = 0
    for key in d.keys():
        len_key = len(key)
        if len_key > max_key_length:
            max_key_length = len_key

    log_format = '{:>'+str(max_key_length)+'} = {}'
    for key, value in d.items():
        out_callback(log_format.format(key, value))


def print_as_title(title, decoration_char, upper_decoration=False, out_callback=sys.stdout.write):
    if upper_decoration:
        out_callback(decoration_char*len(title))
    out_callback(title)
    out_callback(decoration_char*len(title))


def get_combined_settings():
    plugin_settings = sublime.load_settings("ProjectEnvironment.sublime-settings")
    plugin_settings_dic = {}
    for key in ('print_output', 'set_sublime_variables', 'sublime_variables_prefix', 'sublime_variables_capitalized'):
        plugin_settings_dic[key] = plugin_settings.get(key)

    proj_env_setts = get_project_env_settings()
    if proj_env_setts:
        return combine_dicts(plugin_settings_dic, proj_env_setts)
    else:
        return plugin_settings


def get_active_project_name():
    window_vars = sublime.active_window().extract_variables()
    return window_vars.get('project_base_name', None)


def get_project_env_settings():
    proj_data = sublime.active_window().project_data()
    if not proj_data:
        return {}
    try:
        proj_env_setts = proj_data['settings']['project_environment']
        return proj_env_setts
    except KeyError:
        return {}



class ProjectEnvironmentLog:
    def __init__(self, window):
        self.window = window
        self.panel = window.find_output_panel('project_environment_log')
        if not self.panel:
            self.panel = window.create_output_panel('project_environment_log')

        settings = self.panel.settings()
        settings.set('auto_indent', False)
        settings.set('smart_indent', False)
        settings.set('indent_to_bracket', False)
        settings.set('indent_subsequent_lines', False)
        settings.set('trim_automatic_white_space', False)
        settings.set('copy_with_empty_selection', True)

        self.mute = False

    def __call__(self, *msgs):
        if self.mute: return

        full_msg = ' '.join([str(m) for m in msgs])+'\n'
        self.panel.run_command('insert', {'characters': full_msg})

    def clear(self):
        self.panel.run_command('select_all')
        self.panel.run_command('insert', {'characters': ''})

    def show(self):
        self.window.run_command('show_panel', {'panel': 'output.project_environment_log'})

    def hide(self):
        self.window.run_command('hide_panel', {'panel': 'output.project_environment_log'})


class ProjectEnvironmentListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwds):
        super(ProjectEnvironmentListener, self).__init__(*args, **kwds)

        self.active_window  = None
        self.active_project = None

    def on_activated_async(self, view):
        if self.active_window == sublime.active_window():
            if self.active_project == sublime.active_window().project_file_name():
                return
        self.active_window  = sublime.active_window()
        self.active_project = sublime.active_window().project_file_name()

        sublime.active_window().run_command('set_project_environment')
        sublime.active_window().run_command('update_project_data')

    def on_post_save(self, view):
        if view.file_name() == sublime.active_window().project_file_name():
            sublime.active_window().run_command('set_project_environment')
            sublime.active_window().run_command('update_project_data')


class SetProjectEnvironmentCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super().__init__(window)
        self.log = ProjectEnvironmentLog(window)

    def is_enabled(self):
        if get_project_env_settings():
            return True
        else:
            return False

    def run(self):
        new_envs = {
            'sublime': {},
            'inline_env': {},
            'command_file_env': {}
        }

        to_default_environment()
        project_settings = get_combined_settings()
        platform = sublime.platform()
        window_vars = self.window.extract_variables()
        platform_settings = project_settings.get(platform, {})

        if project_settings.get('print_output'):
            self.log.mute = False
        else:
            self.log.mute = True

        self.log('\n')
        time_ = datetime.datetime.now().strftime("%H:%M:%S")
        t = 'Updating {}\'s Environment at {}'.format(get_active_project_name(), time_)
        print_as_title(t, '=', True, self.log)
        self.log()

        #--------------------------------------------------#
        #  Collect variables from Sublime itself
        #--------------------------------------------------#
        if project_settings.get('set_sublime_variables'):
            keys = ("project_path", "project", "project_name", "project_base_name", "packages")
            prefix = project_settings.get('sublime_variables_prefix', '')
            capit = project_settings.get('sublime_variables_capitalized', False)
            for key in keys:
                env_key = prefix+key
                if capit:
                    env_key = env_key.upper()
                new_envs['sublime'][env_key] = window_vars[key]

            print_as_title('From Sublime', '-', False, self.log) #, new_envs['sublime'])
            pretty_print_dict(new_envs['sublime'], self.log)
            self.log()

        #--------------------------------------------------#
        #  Collect the variables executing
        #  a shell or batch file
        #--------------------------------------------------#

        env_file = platform_settings.get('env_file')
        if env_file:
            env_file = os.path.expandvars(env_file)
            if env_file.startswith('.'):
                env_file = os.path.abspath(os.path.join(window_vars['project_path'], env_file))

            file_vars = self.collect_variables_from_file(env_file)
            if file_vars:
                new_envs['command_file_env'] = file_vars
                print_as_title('Variables from {}'.format(env_file), '-', False, self.log)
                pretty_print_dict(file_vars, self.log)
                self.log()

        #--------------------------------------------------#
        #  Collect the "inline" variables
        #--------------------------------------------------#

        main_inline_env     = project_settings.get('env', {})
        platform_inline_env = platform_settings.get('env', {})
        combined_inline_env =combine_dicts(main_inline_env, platform_inline_env)

        if combined_inline_env:
            new_envs['inline_env'] = combined_inline_env
            print_as_title('Inline Variables', '-', False, self.log)
            pretty_print_dict(new_envs['inline_env'], self.log)
            self.log()

        #--------------------------------------------------#
        #  Group all the variables together
        #  and set up the new environment
        #--------------------------------------------------#

        all_new_vars = combine_dicts(new_envs['sublime'], new_envs['command_file_env'])
        all_new_vars = combine_dicts(all_new_vars, new_envs['inline_env'])
        for key, value in all_new_vars.items():
            os.environ[key] = value

        print_as_title('Complete Project Environment', '-', False, self.log)
        pretty_print_dict(all_new_vars, self.log)
        self.log()

    def collect_variables_from_file(self, command_file_path):
        pack_path = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))
        print_env_py = os.path.normpath(os.path.join(pack_path, "utils/print_env.py"))

        popenArguments = {'stdout': subprocess.PIPE, 
                          'stderr': subprocess.PIPE, 
                          'shell': False,
                          'universal_newlines': True}

        if(sublime.platform() == "windows"):
            source_vars = os.path.join(pack_path, "utils/source_vars.bat")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            popenArguments['startupinfo'] = startupinfo
            ingnore_envs = ('PROMPT', )
        else:
            source_vars = os.path.join(pack_path, "utils/source_vars.sh")
            ingnore_envs = ('__PYVENV_LAUNCHER__', 'LC_CTYPE', 'PWD', 'SHLVL', '_')

        popenArguments['args'] = popenArguments['args'] = [source_vars, command_file_path, sys.executable, print_env_py]
        with subprocess.Popen(**popenArguments) as p:

            stdout, stderr = p.communicate()
            if stdout and not stderr:
                new_env = json.loads(stdout)

                result_env = {}
                for key, value in new_env.items():
                    if key in ingnore_envs:
                        continue
                    elif key not in DEFAULT_ENV:
                        result_env[key] = value
                    elif value != DEFAULT_ENV[key]:
                        result_env[key] = value

                return result_env

            elif stderr:
                self.log('__ERROR:__', stderr)
                return {}
            else:
                self.log('__WARNING:__', 'no environment returned')
                return {}


class UpdateProjectDataCommand(sublime_plugin.WindowCommand):
    def run(self):
        data  = self.window.project_data()
        for folder in data['folders']:
            if "path_template" in folder:
                template = folder['path_template']
                resolved = os.path.expandvars(template)
                folder['path'] = resolved
        self.window.set_project_data(data)

    def is_enabled(self):
        data = self.window.project_data()
        if data:
            for folder in data['folders']:
                if "path_template" in folder:
                    return True
        return False

    def is_visible(self):
        return self.is_enabled()


class ClearProjectEnvironmentLogCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super().__init__(window)
        self.log = ProjectEnvironmentLog(window)

    def run(self):
        self.log.clear()

    def is_enabled(self):
        if get_project_env_settings():
            return True
        else:
            return False


class UpdateProjectEnvironmentSettingsCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        data = self.window.project_data()
        if not data:
            return False

        settings_data = data.get('settings')
        if not settings_data:
            return False

        setts = ['print_output', 'set_sublime_variables',
                 'sublime_variables_capitalized', 'sublime_variables_prefix',
                 'env', 'env_file']

        for sett in setts:
            if sett in settings_data:
                return True

        return False

    def is_enabled(self):
        return self.is_visible()


    def run(self):
        data = self.window.project_data()
        settings_data = data.get('settings')
        if not settings_data:
            return

        proj_env = {}

        setts = ['print_output', 'set_sublime_variables', 'sublime_variables_capitalized', 'sublime_variables_prefix']
        for sett in setts:
            if sett in settings_data:
                proj_env[sett] = copy.deepcopy(settings_data[sett])

        old_oss = ('Windows', 'Darwin', 'Linux')
        new_oss = ('windows', 'osx', 'linux')

        for i, old_os in enumerate(old_oss):
            new_os = new_oss[i]
            if "env" in settings_data:
                if old_os in settings_data['env']:
                    proj_env[new_os] = {}
                    proj_env[new_os]['env'] = copy.deepcopy(settings_data['env'][old_os])

            if "env_file" in settings_data:
                if old_os in settings_data['env_file']:
                    if not new_os in proj_env:
                        proj_env[new_os] = {}
                    proj_env[new_os]['env_file'] = copy.deepcopy(settings_data['env_file'][old_os])

        for sett in setts+['env', 'env_file']:
            if sett in data['settings']:
                del data['settings'][sett]
        data['settings']['project_environment'] = proj_env

        self.window.set_project_data(data)