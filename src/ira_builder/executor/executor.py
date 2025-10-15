# File based from: https://github.com/microsoft/autogen/blob/main/autogen/coding/local_commandline_code_executor.py
# Credit to original authors
# Simplified for workflow executor usage

import asyncio
import logging
import os
import sys
import warnings
from hashlib import sha256
from pathlib import Path
from string import Template
from types import SimpleNamespace
from typing import Any, Callable, ClassVar, List, Optional, Sequence, Union

from .core.base import CodeExecutor, CodeBlock
from .core.func_with_reqs import FunctionWithRequirements, FunctionWithRequirementsStr
from .core.cancellation import CancellationToken
from .core.common import (
    PYTHON_VARIANTS,
    CommandLineCodeResult,
    build_python_functions_file,
    get_file_name_from_content,
    lang_to_cmd,
    silence_pip,
    to_stub,
)
from typing_extensions import ParamSpec

__all__ = ("PythonScriptExecutor",)

A = ParamSpec("A")


class PythonScriptExecutor(CodeExecutor):
    """A code executor class that executes Python scripts through a local command line
    environment.

    .. danger::

        This will execute code on the local machine. If being used with LLM generated code, caution should be used.

    Each code block is saved as a file and executed in a separate process in
    the working directory, and a unique file is generated and saved in the
    working directory for each code block.
    The code blocks are executed in the order they are received.
    Currently the only supported languages is Python and shell scripts.
    For Python code, use the language "python" for the code block.
    For shell scripts, use the language "bash", "shell", or "sh" for the code
    block.

    .. note::

        On Windows, the event loop policy must be set to `WindowsProactorEventLoopPolicy` to avoid issues with subprocesses.

        .. code-block:: python

            import sys
            import asyncio

            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    Args:
        timeout (int): The timeout for the execution of any single code block. Default is 60.
        work_dir (str): The working directory for the code execution. If None,
            a default working directory will be used. The default working
            directory is the current directory ".".
        functions (List[Union[FunctionWithRequirements[Any, A], Callable[..., Any]]]): A list of functions that are available to the code executor. Default is an empty list.
        functions_module (str, optional): The name of the module that will be created to store the functions. Defaults to "functions".
        virtual_env_context (Optional[SimpleNamespace], optional): The virtual environment context. Defaults to None.

    Example:

        .. code-block:: python

            import asyncio
            from pathlib import Path
            from workflow_executor.nodes.python_executor import PythonScriptExecutor, CodeBlock

            async def example():
                work_dir = Path("coding")
                work_dir.mkdir(exist_ok=True)

                executor = PythonScriptExecutor(work_dir=work_dir)
                result = await executor.execute_code_blocks(
                    code_blocks=[
                        CodeBlock(language="python", code="print('Hello World!')"),
                    ]
                )
                print(result.output)

            asyncio.run(example())
    """

    SUPPORTED_LANGUAGES: ClassVar[List[str]] = [
        "bash",
        "shell", 
        "sh",
        "python",
    ]
    
    FUNCTION_PROMPT_TEMPLATE: ClassVar[str] = """You have access to the following user defined functions. They can be accessed from the module called `$module_name` by their function names.

For example, if there was a function called `foo` you could import it by writing `from $module_name import foo`

$functions"""

    def __init__(
        self,
        timeout: int = 60,
        work_dir: Union[Path, str] = Path("."),
        functions: Sequence[
            Union[
                FunctionWithRequirements[Any, A],
                Callable[..., Any],
                FunctionWithRequirementsStr,
            ]
        ] = [],
        functions_module: str = "functions",
        virtual_env_context: Optional[SimpleNamespace] = None,
        auto_cleanup: bool = True
    ):
        self._auto_cleanup = auto_cleanup
        if timeout < 1:
            raise ValueError("Timeout must be greater than or equal to 1.")

        if isinstance(work_dir, str):
            work_dir = Path(work_dir)

        if not functions_module.isidentifier():
            raise ValueError("Module name must be a valid Python identifier")

        self._functions_module = functions_module

        work_dir.mkdir(exist_ok=True)

        self._timeout = timeout
        self._work_dir: Path = work_dir

        self._functions = functions
        # Setup could take some time so we intentionally wait for the first code block to do it.
        if len(functions) > 0:
            self._setup_functions_complete = False
        else:
            self._setup_functions_complete = True

        self._virtual_env_context: Optional[SimpleNamespace] = virtual_env_context

        

    def format_functions_for_prompt(self, prompt_template: str = None) -> str:
        """Format the functions for a prompt.

        The template includes two variables:
        - `$module_name`: The module name.
        - `$functions`: The functions formatted as stubs with two newlines between each function.

        Args:
            prompt_template (str): The prompt template. Default is the class default.

        Returns:
            str: The formatted prompt.
        """
        if prompt_template is None:
            prompt_template = self.FUNCTION_PROMPT_TEMPLATE
            
        template = Template(prompt_template)
        return template.substitute(
            module_name=self._functions_module,
            functions="\n\n".join([to_stub(func) for func in self._functions]),
        )

    @property
    def functions_module(self) -> str:
        """The module name for the functions."""
        return self._functions_module

    @property
    def timeout(self) -> int:
        """The timeout for code execution."""
        return self._timeout

    @property
    def work_dir(self) -> Path:
        """The working directory for the code execution."""
        return self._work_dir

    async def _setup_functions(self, cancellation_token: Optional[CancellationToken] = None) -> None:
        func_file_content = build_python_functions_file(self._functions)
        func_file = self._work_dir / f"{self._functions_module}.py"
        func_file.write_text(func_file_content)

        # Collect requirements
        lists_of_packages = [x.python_packages for x in self._functions if isinstance(x, FunctionWithRequirements)]
        flattened_packages = [item for sublist in lists_of_packages for item in sublist]
        required_packages = list(set(flattened_packages))
        if len(required_packages) > 0:
            logging.info("Ensuring packages are installed in executor.")

            cmd_args = ["-m", "pip", "install"]
            cmd_args.extend(required_packages)

            if self._virtual_env_context:
                py_executable = self._virtual_env_context.env_exe
            else:
                py_executable = sys.executable

            task = asyncio.create_task(
                asyncio.create_subprocess_exec(
                    py_executable,
                    *cmd_args,
                    cwd=self._work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            )
            
            if cancellation_token:
                cancellation_token.link_future(task)
                
            try:
                proc = await task
                stdout, stderr = await asyncio.wait_for(proc.communicate(), self._timeout)
            except asyncio.TimeoutError as e:
                raise ValueError("Pip install timed out") from e
            except asyncio.CancelledError as e:
                raise ValueError("Pip install was cancelled") from e

            if proc.returncode is not None and proc.returncode != 0:
                raise ValueError(f"Pip install failed. {stdout.decode()}, {stderr.decode()}")

        # Attempt to load the function file to check for syntax errors, imports etc.
        exec_result = await self._execute_code_dont_check_setup(
            [CodeBlock(code=func_file_content, language="python")], cancellation_token
        )

        if exec_result.exit_code != 0:
            raise ValueError(f"Functions failed to load: {exec_result.output}")

        self._setup_functions_complete = True

    async def execute_code_blocks(
        self, code_blocks: List[CodeBlock], cancellation_token: Optional[CancellationToken] = None
    ) -> CommandLineCodeResult:
        """Execute the code blocks and return the result.

        Args:
            code_blocks (List[CodeBlock]): The code blocks to execute.
            cancellation_token (CancellationToken, optional): a token to cancel the operation

        Returns:
            CommandLineCodeResult: The result of the code execution.
        """

        if not self._setup_functions_complete:
            await self._setup_functions(cancellation_token)

        return await self._execute_code_dont_check_setup(code_blocks, cancellation_token)
    
    async def _execute_code_dont_check_setup(
    self, code_blocks: List[CodeBlock], cancellation_token: Optional[CancellationToken] = None
) -> CommandLineCodeResult:
        """
        Execute the provided code blocks in the local command line without re-checking setup.
        Returns a CommandLineCodeResult indicating success or failure.
        """
        logs_all: str = ""
        file_names: List[Path] = []
        exitcode = 0
        
        try:
            for code_block in code_blocks:
                lang, code = code_block.language, code_block.code
                lang = lang.lower()

                # Remove pip output where possible
                code = silence_pip(code, lang)

                # Normalize python variants to "python"
                if lang in PYTHON_VARIANTS:
                    lang = "python"

                # Abort if not supported
                if lang not in self.SUPPORTED_LANGUAGES:
                    exitcode = 1
                    logs_all += "\n" + f"unknown language {lang}"
                    break

                # Try extracting a filename (if present)
                try:
                    filename = get_file_name_from_content(code, self._work_dir)
                except ValueError:
                    return CommandLineCodeResult(
                        exit_code=1,
                        output="Filename is not in the workspace",
                        code_file=None,
                    )

                # If no filename is found, create one
                if filename is None:
                    code_hash = sha256(code.encode()).hexdigest()
                    if lang.startswith("python"):
                        ext = "py"
                    else:
                        ext = lang

                    filename = f"tmp_code_{code_hash}.{ext}"

                written_file = (self._work_dir / filename).resolve()
                with written_file.open("w", encoding="utf-8") as f:
                    f.write(code)
                file_names.append(written_file)

                # Build environment
                env = os.environ.copy()
                if self._virtual_env_context:
                    virtual_env_bin_abs_path = os.path.abspath(self._virtual_env_context.bin_path)
                    env["PATH"] = f"{virtual_env_bin_abs_path}{os.pathsep}{env['PATH']}"

                # Decide how to invoke the script
                if lang == "python":
                    program = (
                        os.path.abspath(self._virtual_env_context.env_exe) if self._virtual_env_context else sys.executable
                    )
                    extra_args = [str(written_file.absolute())]
                else:
                    # Get the appropriate command for the language
                    program = lang_to_cmd(lang)
                    # Shell commands (bash, sh, etc.)
                    extra_args = [str(written_file.absolute())]

                # Create a subprocess and run
                task = asyncio.create_task(
                    asyncio.create_subprocess_exec(
                        program,
                        *extra_args,
                        cwd=self._work_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=env,
                    )
                )
                
                if cancellation_token:
                    cancellation_token.link_future(task)

                try:
                    proc = await task
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), self._timeout)
                    exitcode = proc.returncode or 0
                except asyncio.TimeoutError:
                    # Try to kill the process
                    try:
                        proc.kill()
                        await proc.wait()
                    except:
                        pass
                    logs_all += "\nTimeout"
                    exitcode = 124
                    break
                except asyncio.CancelledError:
                    logs_all += "\nCancelled"
                    exitcode = 125
                    break

                logs_all += stderr.decode()
                logs_all += stdout.decode()

                if exitcode != 0:
                    break

            code_file = str(file_names[0]) if file_names else None
            return CommandLineCodeResult(exit_code=exitcode, output=logs_all, code_file=code_file)
        
        finally:
            if self._auto_cleanup:
                await self._cleanup_temp_files(file_names)
            

    async def _cleanup_temp_files(self, file_names: List[Path]) -> None:
        """Clean up temporary files created during execution."""
        for file_path in file_names:
            try:
                if file_path.exists() and file_path.name.startswith('tmp_code_'):
                    file_path.unlink()  # Delete the file
                    logging.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                # Log but don't fail the execution due to cleanup issues
                logging.warning(f"Failed to cleanup temporary file {file_path}: {e}")

    # async def _execute_code_dont_check_setup(
    #     self, code_blocks: List[CodeBlock], cancellation_token: Optional[CancellationToken] = None
    # ) -> CommandLineCodeResult:
    #     """
    #     Execute the provided code blocks in the local command line without re-checking setup.
    #     Returns a CommandLineCodeResult indicating success or failure.
    #     """
    #     logs_all: str = ""
    #     file_names: List[Path] = []
    #     exitcode = 0

    #     for code_block in code_blocks:
    #         lang, code = code_block.language, code_block.code
    #         lang = lang.lower()

    #         # Remove pip output where possible
    #         code = silence_pip(code, lang)

    #         # Normalize python variants to "python"
    #         if lang in PYTHON_VARIANTS:
    #             lang = "python"

    #         # Abort if not supported
    #         if lang not in self.SUPPORTED_LANGUAGES:
    #             exitcode = 1
    #             logs_all += "\n" + f"unknown language {lang}"
    #             break

    #         # Try extracting a filename (if present)
    #         try:
    #             filename = get_file_name_from_content(code, self._work_dir)
    #         except ValueError:
    #             return CommandLineCodeResult(
    #                 exit_code=1,
    #                 output="Filename is not in the workspace",
    #                 code_file=None,
    #             )

    #         # If no filename is found, create one
    #         if filename is None:
    #             code_hash = sha256(code.encode()).hexdigest()
    #             if lang.startswith("python"):
    #                 ext = "py"
    #             else:
    #                 ext = lang

    #             filename = f"tmp_code_{code_hash}.{ext}"

    #         written_file = (self._work_dir / filename).resolve()
    #         with written_file.open("w", encoding="utf-8") as f:
    #             f.write(code)
    #         file_names.append(written_file)

    #         # Build environment
    #         env = os.environ.copy()
    #         if self._virtual_env_context:
    #             virtual_env_bin_abs_path = os.path.abspath(self._virtual_env_context.bin_path)
    #             env["PATH"] = f"{virtual_env_bin_abs_path}{os.pathsep}{env['PATH']}"

    #         # Decide how to invoke the script
    #         if lang == "python":
    #             program = (
    #                 os.path.abspath(self._virtual_env_context.env_exe) if self._virtual_env_context else sys.executable
    #             )
    #             extra_args = [str(written_file.absolute())]
    #         else:
    #             # Get the appropriate command for the language
    #             program = lang_to_cmd(lang)
    #             # Shell commands (bash, sh, etc.)
    #             extra_args = [str(written_file.absolute())]

    #         # Create a subprocess and run
    #         task = asyncio.create_task(
    #             asyncio.create_subprocess_exec(
    #                 program,
    #                 *extra_args,
    #                 cwd=self._work_dir,
    #                 stdout=asyncio.subprocess.PIPE,
    #                 stderr=asyncio.subprocess.PIPE,
    #                 env=env,
    #             )
    #         )
            
    #         if cancellation_token:
    #             cancellation_token.link_future(task)

    #         try:
    #             proc = await task
    #             stdout, stderr = await asyncio.wait_for(proc.communicate(), self._timeout)
    #             exitcode = proc.returncode or 0
    #         except asyncio.TimeoutError:
    #             # Try to kill the process
    #             try:
    #                 proc.kill()
    #                 await proc.wait()
    #             except:
    #                 pass
    #             logs_all += "\nTimeout"
    #             exitcode = 124
    #             break
    #         except asyncio.CancelledError:
    #             logs_all += "\nCancelled"
    #             exitcode = 125
    #             break

    #         logs_all += stderr.decode()
    #         logs_all += stdout.decode()

    #         if exitcode != 0:
    #             break

    #     code_file = str(file_names[0]) if file_names else None
    #     return CommandLineCodeResult(exit_code=exitcode, output=logs_all, code_file=code_file)

    async def restart(self) -> None:
        """Restart the code executor."""
        warnings.warn(
            "Restarting Python script executor is not supported. No action is taken.",
            stacklevel=2,
        )