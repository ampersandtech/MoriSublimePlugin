######
 # Copyright 2016-present Mori, Inc.
 #
 # 
 ######

import os
import re
import json
import sublime, sublime_plugin

HAS_REL_PATH_RE = re.compile(r"\.?\.?\/");
reqLine = re.compile("(?:\/\/)?(?:\/\*)?(?: )?var [A-Z]\w*(?: )=(?: )(?:app)?[rR]equire\('[^ ']*'\);(?: *)(?:\*\/)?(?: *)");
reqIgnore = re.compile("(?:\/\/)?(?:\/\*)?(?: )?var [a-z]\w*(?: )=(?: )(?:app)?[rR]equire\('[^ ']*'\);(?: *)(?:\*\/)?(?: *)");
esLintLine = re.compile("^\/\* eslint-disable.*\*\/$");
reqName = re.compile(".*var (\w*).*");

class ModuleLoader():
  def __init__(self, file_name):
    """Constructor for ModuleLoader."""
    self.file_name = file_name
    self.project_folder = self.get_project_folder()

    # If there is no package.json, show error
    if not self.has_package():
      return sublime.error_message(
        'You must have a package.json and or bower.json file '
        'in your projects root directory'
      )

  def get_project_folder(self) -> str:
    """Get the root project folder."""
    # Walk through directories if we didn't find it easily
    dirname = os.path.dirname(self.file_name)
    while dirname:
      pkg = os.path.join(dirname, 'package.json')
      if os.path.exists(pkg):
        return dirname
      parent = os.path.abspath(os.path.join(dirname, os.pardir))
      if parent == dirname:
        break
      dirname = parent

    try:
      project_data = sublime.active_window().project_data()
      if project_data:
        first_folder = project_data['folders'][0]['path']
        return first_folder
    except:
      pass

  def has_package(self):
    """Check if the package.json is in the project directory."""
    return os.path.exists(
      os.path.join(self.project_folder, 'package.json')
    )

  def get_file_list(self):
    """Return the list of dependencies and local files."""
    files = self.get_local_files() + self.get_dependencies()
    
    return files

  def get_local_files(self):
    """Load the list of local files."""
    # Don't throw errors if invoked in a view without
    # a filename like the console
    local_files = []
    if not self.file_name:
      return []

    dirname = os.path.dirname(self.file_name)
    exclude = ['node_modules', '.git' ,'backups', 'builds', 'branding', 'tmp', 'cache', 'clientcache', 'ios', 's3mirror']
    for root, dirs, files in os.walk(self.project_folder, topdown=True):
      if os.path.samefile(root, self.project_folder):
        dirs[:] = [d for d in dirs if d not in exclude]

      for file_name in files:
        if file_name[0] is not '.':
          file_name = "%s/%s" % (root, file_name)
          file_name = os.path.relpath(file_name, self.project_folder)

          if file_name == os.path.basename(self.file_name):
            continue

          if not HAS_REL_PATH_RE.match(file_name):
            file_name = "./%s" % file_name

        if file_name[0] is '.' and file_name[1] is not '/':
          continue;

        local_files.append(file_name)
    return local_files

  def get_dependencies(self):
    """Parse the package.json file into a list of dependencies."""
    package = os.path.join(self.project_folder, 'package.json')
    package_json = json.load(open(package, 'r', encoding='UTF-8'))
    dependency_types = (
      'dependencies',
      'devDependencies',
      'optionalDependencies'
    )
    dependencies = self.get_dependencies_with_type(
      dependency_types, package_json
    )
    modules_path = os.path.join(self.project_folder, 'node_modules')
    #dep_files = self.get_dependency_files(dependencies, modules_path)
    return dependencies

  def get_dependencies_with_type(self, dependency_types, json):
        """Common function for adding dependencies (bower or package.json)."""
        dependencies = []
        for dependency_type in dependency_types:
            if dependency_type in json:
                dependencies += json[dependency_type].keys()
        return dependencies

  def get_dependency_files(self, dependencies, modules_path):
    """Walk through deps to allow requiring of files in deps package."""
    files_to_return = []
    for dependency in dependencies:
      module_path = os.path.join(modules_path, dependency)
      if not os.path.exists(module_path):
        continue

      walk = os.walk(module_path)
      for root, dirs, files in walk:
        if 'node_modules' in dirs:
          dirs.remove('node_modules')
        for file_name in files:
          basename = os.path.basename(file_name)
          if not file_name.endswith('.js') or basename == 'index.js':
            continue
          full_path = os.path.join(root, file_name)
          rel_path = os.path.relpath(full_path, module_path)
          files_to_return.append(os.path.join(dependency, rel_path))
    return files_to_return

class appRequireDocCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.module_loader = ModuleLoader(self.view.file_name());
    self.files = self.module_loader.get_file_list();
    sublime.active_window().show_quick_panel(
      self.files, self.on_done_call_func(self.files, self.insertAppRequire));

  def insertAppRequire(self, module):
    pos = self.view.find("^'use strict';$", 0).begin();

    if pos == -1:
      pos = 0;
    else:
      pos+=1;

    lastGoodPos = pos;
    pad = 0;

    while (pos < self.view.size()):
      area = self.view.line(pos);
      line = self.view.substr(area);
      line.strip();

      if re.match(reqLine, line):
        break;

      if re.match(reqIgnore, line) or re.match(esLintLine, line):
        lastGoodPos = area.end()+1;

      pos = area.end()+1;

    if pos >= self.view.size():
      pos = lastGoodPos;
      pad = 1;

    self.view.run_command('app_require_insert_helper', {
      'args': {
        'module': module,
        'pos':pos,
        'highlight':0,
        'pad':pad,
      }
    });

  def on_done_call_func(self, choices, func):
    """Return a function which is used with sublime list picking."""
    def on_done(index):
        if index >= 0:
            return func(choices[index])

    return on_done

class appRequireCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.module_loader = ModuleLoader(self.view.file_name())
    self.files = self.module_loader.get_file_list()
    sublime.active_window().show_quick_panel(
      self.files, self.on_done_call_func(self.files, self.insertAppRequire));

  def insertAppRequire(self, module):
    self.view.run_command('app_require_insert_helper', {
      'args': {
        'module': module,
        'pos': self.view.sel()[0].begin(),
        'highlight':1,
        'pad':0,
      }
    });
    

  def on_done_call_func(self, choices, func):
    """Return a function which is used with sublime list picking."""
    def on_done(index):
        if index >= 0:
            return func(choices[index])

    return on_done

class appRequireInsertHelper(sublime_plugin.TextCommand):
  def varNameFromModule(self, module):
    if (module.rfind('/') != -1):
      module = module[module.rfind('/')+1:];

    if (module.find('.') != -1):
      module = module[:module.find('.')];

    while module.find('_') != -1:
      idx = module.find('_');
      module = module[:idx] + module[idx+1].upper() + module[idx+2:];
    # cap first letter
    module = module[0].upper() + module[1:];
    return module;

  def moduleNameFromLine(self, line):
    line = line.lower();
    match = re.match(reqName, line);
    if match:
      return match.group(1);
    else:
      return line;

  def run (self, edit, args):
    view = self.view
    module = args['module'];
    pos = args['pos'];

    entry = "require('" + module + "');";

    if module[-3:] == '.js':
      module = module[:-3];

    if module[0] == '.':
      entry = "appRequire('" + module[2:] + "');";

    if (module[0] == '/'):
      entry = "appRequire('" + module[1:] + "');";

    linepos = view.line(pos);
    line = view.substr(linepos);
    

    if line == '' or re.match(reqLine, line):
      
      entry = 'var ' + self.varNameFromModule(module) + ' = ' + entry;
      lines = [entry];
      idx = linepos.a-1;
      replace = linepos;

      if re.match(reqLine, line):
        lines.append(line);

      while idx>=0:
        line = view.substr(view.line(idx));
        if re.match(reqLine, line):
          lines.append(line);
          replace = replace.cover(view.line(idx));
          idx = view.line(idx).begin()-1;

        else:
          break;

      idx = linepos.b+1;
      while idx<self.view.size():
        line = view.substr(view.line(idx));
        if (re.match(reqLine, line)):
          lines.append(line);
          replace = replace.cover(view.line(idx));
          idx = view.line(idx).end()+1;
        else:
          break;

      lines = sorted(set(lines), key=self.moduleNameFromLine);

      if args['pad']:
        lines.append('');
        lines.insert(0, '');
      
      self.view.replace(edit, replace, '\n'.join(str(x) for x in lines));

      if args['highlight'] == 1:
        higlight = self.view.find(entry, replace.begin(), sublime.LITERAL);
        self.view.sel().clear();
        self.view.sel().add(higlight);
    else:
      self.view.insert(edit, pos, entry);

