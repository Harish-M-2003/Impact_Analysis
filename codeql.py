from subprocess import run
from enums.LanguageSupported import LanguageSupported
from pathlib import Path
from query import Query
from csv import writer
from call_graph import CallGraph

class CodeQL:

    def __init__(self, path: Path, db_name: str, language: LanguageSupported):

        self.__db_name = None
        self.set_db_name(db_name)

        self.__language = None
        self.set_language(language)

        self.__path = None
        self.set_path(path)

        if not self.db_exists():
            self.init()

    def get_language(self) -> str:

        return self.__language.value
    
    def get_path(self):

        return self.__path
    
    def get_db_name(self):

        return self.__db_name
    
    def set_db_name(self, db_name: str):

        if db_name:
            self.__db_name = db_name
        else:
            raise ValueError("ParameterValueError : db_name cannot be [None, '']")
        
    def set_language(self, language: LanguageSupported):

        if language:
            self.__language = language
        else:
            raise ValueError("ParameterValueError : language cannot be [None, '']")
        
    def set_path(self, path: Path):

        if path:
            self.__path = path
        else:
            raise ValueError("ParameterValueError : path cannot be [None, '']")
    
    def init(self) -> None:

        create_db_command = [
            'codeql', 
            'database',
            'create', 
            f'{self.get_db_name()}', 
            f'-l={self.get_language()}', 
            f'-s={self.get_path()}'
        ]
        
        
        cli_output = run(create_db_command, capture_output=True, check=True, text=True)
        return cli_output

    def __execute_qurey(self, query: Query):

        query_execution_command= ['codeql', 'query', 'run']
        
        config = query.get_config()
        if config:
            query_execution_command.append(
                f'--external=targetMethodName={config}'
            )
        
        query_execution_command.extend([
            f'--database={self.get_db_name()}',
            f'{query.get_path()}',
            f'-o=output.bqrs'
        ])

        
        cli_output= run(query_execution_command)

        decode_command= ['codeql', 'bqrs', 'decode', 'output.bqrs', '--format=json']

        cli_output= run(decode_command, capture_output=True, text=True, check=True)

        return cli_output.stdout


    def overwrite(self):

        db_overwrite_command = [
            'codeql', 
            'database',
            'create',
            '--overwrite', 
            f'{self.get_db_name()}', 
            f'-l={self.get_language()}', 
            f'-s={self.get_path()}'
        ]

        cli_ouput = run(db_overwrite_command)

    def get_callers_of(self, delta_funcs):

        delta_changes = []

        for delta_func in delta_funcs:
            delta_changes.append(delta_func.name[delta_func.name.find(":") + 2:])
        
        with open("queries/codeql/config/get_callers_of_delta_functions.csv","w",newline="") as f:
            w = writer(f)

            for func in delta_changes:
                w.writerow([func])

        self.__execute_qurey(Query.build('codeql' , 'get_callers_of_delta_functions'))

    
    def get_impact(self, graph: CallGraph):

        nodes = graph.get_graph().nodes

        with open("queries/codeql/config/get_callers_of_delta_functions.csv","w",newline="") as f:
            w = writer(f)

            for function_name, meta_data in nodes(data=True):
                # w.writerow([meta_data["class_name"] + "::" + function_name + str(meta_data["parameters"])])
                w.writerow([meta_data["function_name"]])

        cli_output = self.__execute_qurey(Query.build("codeql", "get_callers_of_delta_functions"))

        return cli_output

    def db_exists(self):
        
        db_path = Path(self.get_db_name())

        if not db_path.exists():
            return False

        return (
            db_path.is_dir()
            and (db_path / "codeql-database.yml").exists()
        )