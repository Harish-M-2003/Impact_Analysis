from pathlib import Path

class Query:

    def __init__(self, query_path, query_config):

        self.__query_path= None
        self.set_path(query_path)

        self.__query_config= None
        self.set_query(query_config)

    def set_path(self, path: Path):

        if path:
            self.__query_path= path
        else:
            raise ValueError("QueryPathArgumentValueError : path cannot be [None, '']")
    
    def set_query(self, config):

        if config:
            self.__query_config = config
        else:
            raise ValueError("QueryConfigArgumentValueError : config cannot be [None, '']")
    
    def get_config(self):

        return self.__query_config

    def get_path(self):

        return self.__query_path
    
    @staticmethod
    def build(query_engine, query_name):

        match query_name:
                
            case 'get_callers_of_delta_functions':

                if query_engine.lower() == 'codeql':

                    query_path = 'queries/' + query_engine.lower() + f'/query/{query_name}.ql'
                    query_config = 'queries/' + query_engine.lower() + f'/config/{query_name}.csv'

                    return Query(query_path, query_config)