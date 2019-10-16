from vparser import *
import time
import os


class VWorkspace:

    def __init__(self, code_folders, module_folders=None, load_code_tests=False, load_module_tests=False):
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
        self.load_code_tests = load_code_tests
        self.load_module_tests = load_module_tests

        self.parser = VParser

        # Handle the builtin module
        if 'builtin' not in self.module_files:
            self.module_files['builtin'] = []
        b = self.load_module('builtin')
        assert b is not None, "Failed to load builtin module!"

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

        self.types = []

        # Make sure we ignore the builtin as a root module
        self.root_module = None

    def add_type(self, xtype):
        if xtype in self.types:
            xtype = self.types[self.types.index(xtype)]
        else:
            self.types.append(xtype)
        return xtype

    def load_module(self, name: str):
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

        def parse_folder(dir, load_tests):
            good = True
            got_any = False
            for file in os.listdir(dir):
                file = os.path.join(dir, file)

                if not file.endswith('.v'):
                    continue

                # Only load test files when needed
                if file.endswith('_test.v') and not load_tests:
                    continue
                    
                # TODO: platform specific files

                with open(file, 'r') as f:
                    reporter = ErrorReporter(file)
                    got_any = True
                    try:
                        # TODO: Only if timing
                        start = time.time()
                        parse_tree = self.parser.parse(f.read())
                        end = time.time()

                        if not VAstTransformer(reporter, self).transform(parse_tree):
                            good = False
                    except UnexpectedToken as e:

                        expected_transform = {
                            'DEC_NUMBER': 'Decimal Number',
                            'BANG': '!',
                            'NAME': 'Identifier',
                            'RBRACE': '}',
                            'LBRACE': '{',
                            'STAR': '*',
                            'STRING': 'String Literal',
                            'AMPERSAND': '&',
                            'MINUS': '-',
                            'TILDE': '~',
                            'LPAR': '(',
                            'RPAR': ')',

                            '_NEWLINE': None,
                        }

                        reporter.reporter(e.line, e.column)('error', 'unexpected token')
                        print('expected:')
                        for expected in e.expected:
                            if expected in expected_transform:
                                expected = expected_transform[expected]
                            elif expected.startswith('__ANON'):
                                expected = None
                            else:
                                expected = f'{expected.lower()}'

                            if expected is not None:
                                print(f'\t* {expected}')
                        print()
                        good = False

            return good, got_any

        good = True
        got_any = False

        # The main module is always in the code root, anything else would be inside a module
        # so if we want to load the main module, we are gonna load all the files from the code
        # directories
        if module.name == 'main':
            for folder in self.code_folders:
                res_good, res_got_any = parse_folder(folder, self.load_code_tests)
                if not res_good:
                    good = False
                if res_got_any:
                    got_any = True

        # For any other module simply search in the module folders for the
        # path of the module and parse all files in there
        else:
            for folder in self.module_folders:
                dir = os.path.join(folder, name.replace('.', '/'))
                if os.path.exists(dir):
                    res_good, res_got_any = parse_folder(dir, self.load_module_tests)
                    if not res_good:
                        good = False
                    if res_got_any:
                        got_any = True

        if not got_any and name != 'builtin':
            del self.modules[name]
            return f'could not find module `{name}`'

        if not good:
            return f'error while loading module `{name}`'

        return module

    def type_check(self):
        """
        Run the type checking

        This is going to start from the root module, and because we will get into VModules
        imported into the root module, it should type check everything which is relevant
        """
        return self.root_module.type_checking()
