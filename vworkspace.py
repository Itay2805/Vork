from vparser import *
import os

class VWorkspace:

    def __init__(self, module_folders=None):
        """
        :type module_folders: List[str]
        """
        if module_folders is None:
            module_folders = ['./vlib/']

        self.module_folders = module_folders
        self.module_files = {}  # type: Dict[str, List[str]]
        self.modules = {}  # type: Dict[str, VModule]
        self.root_module = None  # type: VModule or None

        self._scan_files()

        self.parser = VParser
        self.transfomer = VAstTransformer(self)

    def _scan_files(self):
        # In each module folder
        for folder in self.module_folders:
            # Iterate all the files
            for path, dir, file in os.walk(folder):
                for filename in file:
                    # files with v extension
                    if filename.lower().endswith(".v"):
                        # read it
                        with open(os.path.join(path, filename), 'r') as f:

                            got = False

                            # Search for module
                            for line in f.readlines():
                                # got module name, add it
                                if line.strip().startswith('module'):
                                    try:
                                        module_name = line.strip().split(' ', 1)[1]
                                        if module_name not in self.module_files:
                                            self.module_files[module_name] = []
                                        self.module_files[module_name].append(os.path.join(path, filename))
                                        got = True
                                        break
                                    finally:
                                        pass

                            # If no module name found assume main
                            if not got:
                                self.module_files['main'].append(os.path.join(path, filename))

        # Handle the builtin module
        if 'builtin' not in self.module_files:
            self.module_files['builtin'] = []
        b = self.load_module('builtin')

        # Some stuff are defined by the compiler, like
        # types, native functions and more, so we add them here
        b.add_type(VI8(False), 'i8')
        b.add_type(VI16(False), 'i16')
        b.add_type(VInt(False), 'int')
        b.add_type(VI64(False), 'i64')
        b.add_type(VI128(False), 'i128')
        b.add_type(VByte(False), 'byte')
        b.add_type(VU16(False), 'u16')
        b.add_type(VU32(False), 'u32')
        b.add_type(VU64(False), 'u64')
        b.add_type(VU128(False), 'u128')
        b.add_type(VBool(False), 'bool')

        b.add_builtin_function(VBuiltinFunction('print', ['int'], []))

        # Make sure we ignore the builtin as a root module
        self.root_module = None

    def load_module(self, name: str) -> VModule:
        """
        Load a module

        This will parse and transform all the source files related to the module
        and populate their module, note that this will not do type checking

        :param name: The module to load
        :returns: The loaded module
        """
        # Check if already has a reference to the module
        assert name in self.module_files, f"module `{name}` does not exists in workspace"
        if name in self.modules:
            return self.modules[name]

        # Create the module
        module = VModule()
        module.set_module_name(name)
        self.modules[name] = module

        # Set the root module
        if self.root_module is None:
            self.root_module = module

        # If not builtin import builtin automatically
        if module.name != 'builtin':
            module.identifiers['builtin'] = self.load_module('builtin')

        # Create parser and parse each file
        for file in self.module_files[name]:
            with open(file, 'r') as f:
                parse_tree = self.parser.parse(f.read())
                self.transfomer.transform(parse_tree)

        return module

    def type_check(self):
        """
        Run the type checking

        This is going to start from the root module, and because we will get into VModules
        imported into the root module, it should type check everything which is relevant
        """
        self.root_module.type_checking()
