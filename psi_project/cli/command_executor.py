import inspect
import shlex

from psi_project.core import utils


class CommandExecutor:
    def __init__(self):
        self.done = False

    async def run_loop(self):
        while not self.done:
            cmd_input = shlex.split(await utils.ainput("> "))
            cmd = cmd_input[0]
            cmd_args = cmd_input[1:]
            method = getattr(self, f"cmd_{cmd}", None)

            if not method or not inspect.iscoroutinefunction(method):
                print(f"Unknown command: {cmd}")
                continue

            argspec = inspect.getfullargspec(method)

            if len(argspec.args) != len(cmd_args):
                print(f"Command {cmd} expects {len(cmd_args)} arguments, but got {len(argspec.args)}")
                continue

            cmd_args_cast = []

            for arg_name, arg_val in zip(argspec.args, cmd_args):
                if arg_name in argspec.annotations:
                    arg_type = argspec.annotations[arg_name]
                    try:
                        cmd_args_cast.append(arg_type(arg_val))
                    except:
                        print(f"Argument '{arg_val}' cannot be cast to type '{arg_type.__name__}'")
                        break
                else:
                    cmd_args_cast.append(arg_val)

            if len(cmd_args) != len(cmd_args_cast):
                continue

            await method(self, *cmd_args_cast)

    async def cmd_exit(self):
        self.done = True
