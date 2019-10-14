from vparser import *
import os


class VWorkspace:

    def __init__(self, code_folders, module_folders=None):
        """
        :type module_folders: List[str] or None
        :type code_folders: List[str] or None
        """

        # By default include vlib
        if module_folders is None:
            module_folders = ['./vlib/']

        assert len(code_folders) > 0, "must have at least one code folder"

        self.module_folders = module_folders
        self.code_folders = code_folders
        self.module_files = {}  # type: Dict[str, List[str]]
        self.modules = {}  # type: Dict[str, VModule]
        self.root_module = None  # type: VModule or None

        self.parser = VParser

        # Handle the builtin module
        if 'builtin' not in self.module_files:
            self.module_files['builtin'] = []
        b = self.load_module('builtin')

        # Some stuff are defined by the compiler, like
        # types, native functions and more, so we add them here
        b.add_type(VIntegerType(8, True), False, 'i8')
        b.add_type(VIntegerType(16, True), False, 'i16')
        b.add_type(VIntegerType(32, True), False, 'int')
        b.add_type(VIntegerType(64, True), False, 'i64')
        b.add_type(VIntegerType(128, True), False, 'i128')
        b.add_type(VIntegerType(8, False), False, 'byte')
        b.add_type(VIntegerType(16, False), False, 'u16')
        b.add_type(VIntegerType(32, False), False, 'u32')
        b.add_type(VIntegerType(64, False), False, 'u64')
        b.add_type(VIntegerType(128, False), False, 'u128')
        b.add_type(VBool(), False, 'bool')

        b.add_builtin_function(VBuiltinFunction('print', ['int'], []))

        # Make sure we ignore the builtin as a root module
        self.root_module = None

    def load_module(self, name: str) -> Optional[VModule]:
        """
        Load a module

        This will parse and transform all the source files related to the module
        and populate their module, note that this will not do type checking

        :param name: The module to load
        :returns: The loaded module
        """
        # Check if already has a reference to the module
        if name in self.modules:
            return self.modules[name]

        # Create the module
        module = VModule()
        module.workspace = self
        module.set_module_name(name)
        self.modules[name] = module

        # Set the root module
        if self.root_module is None:
            self.root_module = module

        # If not builtin import builtin automatically
        if module.name != 'builtin':
            module.identifiers['builtin'] = self.load_module('builtin')

        good = True
        got_any = False

        # The main module is always in the code root, anything else would be inside a module
        # so if we want to load the main module, we are gonna load all the files from the code
        # directories
        if module.name == 'main':
            for folder in self.code_folders:
                for file in os.listdir(folder):
                    file = os.path.join(folder, file)
                    with open(file, 'r') as f:
                        parse_tree = self.parser.parse(f.read())
                        got_any = True
                        if not VAstTransformer(file, self).transform(parse_tree):
                            good = False

        # For any other module simply search in the module folders for the
        # path of the module and parse all files in there
        else:
            for folder in self.module_folders:
                dir = os.path.join(folder, name.replace('.', '/'))
                if os.path.exists(dir):
                    for file in os.listdir(dir):
                        file = os.path.join(folder, file)
                        with open(file, 'r') as f:
                            parse_tree = self.parser.parse(f.read())
                            got_any = True
                            if not VAstTransformer(file, self).transform(parse_tree):
                                good = False

        if not got_any and name != 'builtin':
            del self.modules[name]
            return None

        if not good:
            return None

        return module

    def type_check(self):
        """
        Run the type checking

        This is going to start from the root module, and because we will get into VModules
        imported into the root module, it should type check everything which is relevant
        """
        return self.root_module.type_checking()
