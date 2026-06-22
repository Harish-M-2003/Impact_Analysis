from pydriller import Repository, Commit
from datetime import datetime, timedelta
from typing import List, Any


class GitRepo:
      
    def __init__(self, repo: str, commit_hash: str):
            
        self.__commit_hash = commit_hash
        self.__repo = Repository(repo, self.__commit_hash)

    def get_changed_methods(self):
         
        delta = []
         
        for commit in self.__repo.traverse_commits():
              for modified_file in commit.modified_files:
                    delta.append(modified_file)
        return delta
                        


if __name__ == '__main__':
     
    git = GitRepo('https://github.com/Harish-M-2003/Squig' , '486c1f1cd9c7bcd9c4c65b2a9def210b536e55d9')
    print(git.get_changed_methods())